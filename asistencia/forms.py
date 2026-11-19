from datetime import date
from django import forms
from django.utils.html import escape
from .models import Asistencia, Empleado, Permiso


class EmpleadoForm(forms.ModelForm):
    class Meta:
        model = Empleado
        fields = [
            'dni', 'nombres', 'apellidos', 'cargo', 'area',
            'fecha_ingreso', 'tipo_contrato', 'email_corporativo'
        ]
        widgets = {'fecha_ingreso': forms.DateInput(attrs={'type': 'date'})}

    def clean_cargo(self):
        cargo = (self.cleaned_data.get('cargo') or '').strip()
        if not cargo:
            raise forms.ValidationError('El cargo no puede estar vacío.')
        return escape(cargo)

    def clean_email_corporativo(self):
        correo = (self.cleaned_data.get('email_corporativo') or '').strip().lower()
        if not correo.endswith('@tecnoandes.pe'):
            raise forms.ValidationError('El correo corporativo debe tener el formato @tecnoandes.pe.')
        return correo

    def clean_fecha_ingreso(self):
        f_ing = self.cleaned_data.get('fecha_ingreso')
        if f_ing and f_ing > date.today():
            raise forms.ValidationError('La fecha de ingreso no puede ser futura.')
        return f_ing


class MarcacionAsistenciaForm(forms.ModelForm):
    class Meta:
        model = Asistencia
        fields = ['empleado', 'fecha', 'hora_entrada', 'hora_salida']
        widgets = {
            'fecha': forms.DateInput(attrs={'type': 'date'}),
            'hora_entrada': forms.TimeInput(attrs={'type': 'time'}),
            'hora_salida': forms.TimeInput(attrs={'type': 'time'}),
        }

    def clean(self):
        cleaned = super().clean()
        empleado = cleaned.get('empleado')
        fecha = cleaned.get('fecha')
        h_entrada = cleaned.get('hora_entrada')
        h_salida = cleaned.get('hora_salida')

        if h_entrada and h_salida and h_salida <= h_entrada:
            self.add_error('hora_salida', 'La hora de salida debe ser posterior a la hora de entrada.')

        if empleado and fecha and not self.instance.pk:
            abierta = Asistencia.objects.filter(
                empleado=empleado, fecha=fecha, hora_salida__isnull=True
            ).exists()
            if abierta:
                raise forms.ValidationError('Ya existe una entrada registrada hoy sin hora de salida.')

        return cleaned


class PermisoForm(forms.ModelForm):
    class Meta:
        model = Permiso
        fields = ['empleado', 'tipo', 'fecha_inicio', 'fecha_fin', 'motivo', 'adjunto_descripcion']
        widgets = {
            'fecha_inicio': forms.DateInput(attrs={'type': 'date'}),
            'fecha_fin': forms.DateInput(attrs={'type': 'date'}),
            'motivo': forms.Textarea(attrs={'rows': 3}),
        }

    def clean_motivo(self):
        motivo = escape((self.cleaned_data.get('motivo') or '').strip())
        if len(motivo) < 30:
            raise forms.ValidationError('El motivo detallado debe tener al menos 30 caracteres.')
        return motivo

    def clean(self):
        cleaned = super().clean()
        empleado = cleaned.get('empleado')
        f_ini = cleaned.get('fecha_inicio')
        f_fin = cleaned.get('fecha_fin')

        if f_ini and f_fin and f_fin < f_ini:
            self.add_error('fecha_fin', 'La fecha de fin debe ser mayor o igual a la fecha de inicio.')

        if empleado and f_ini and f_fin:
            solapados = Permiso.objects.filter(
                empleado=empleado,
                fecha_inicio__lte=f_fin,
                fecha_fin__gte=f_ini,
            ).exclude(estado='rechazado').exists()
            if solapados:
                raise forms.ValidationError('El empleado ya tiene un permiso registrado en ese rango de fechas.')

            dias_solicitados = (f_fin - f_ini).days + 1
            if dias_solicitados > empleado.dias_vacaciones_disponibles:
                raise forms.ValidationError(
                    f'Días insuficientes ({dias_solicitados} solicitados vs {empleado.dias_vacaciones_disponibles} disponibles).'
                )

        return cleaned