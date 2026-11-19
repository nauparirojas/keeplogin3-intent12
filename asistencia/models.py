from datetime import date, datetime
from django.contrib.auth.models import User
from django.db import models
from django.utils import timezone


class Area(models.Model):
    AREAS_CHOICES = [
        ('Sistemas', 'Sistemas'),
        ('Contabilidad', 'Contabilidad'),
        ('Ventas', 'Ventas'),
        ('Logística', 'Logística'),
        ('RRHH', 'RRHH'),
    ]
    nombre = models.CharField(max_length=40, choices=AREAS_CHOICES, unique=True)

    def __str__(self):
        return self.nombre


class Empleado(models.Model):
    CONTRATOS = [('planilla', 'Planilla'), ('locacion', 'Locación')]
    usuario = models.OneToOneField(User, on_delete=models.SET_NULL, null=True, blank=True)
    dni = models.CharField(max_length=8, unique=True)
    nombres = models.CharField(max_length=100)
    apellidos = models.CharField(max_length=100)
    cargo = models.CharField(max_length=80)
    area = models.ForeignKey(Area, on_delete=models.CASCADE, related_name='empleados')
    fecha_ingreso = models.DateField()
    tipo_contrato = models.CharField(max_length=15, choices=CONTRATOS)
    email_corporativo = models.EmailField()
    dias_vacaciones_tomados = models.PositiveIntegerField(default=0)

    def __str__(self):
        return f"{self.apellidos}, {self.nombres} ({self.area})"

    @property
    def antiguedad_texto(self):
        hoy = date.today()
        meses_totales = (hoy.year - self.fecha_ingreso.year) * 12 + (hoy.month - self.fecha_ingreso.month)
        if hoy.day < self.fecha_ingreso.day:
            meses_totales -= 1
        meses_totales = max(0, meses_totales)
        return f"{meses_totales // 12} años, {meses_totales % 12} meses"

    @property
    def dias_vacaciones_disponibles(self):
        return max(0, 30 - self.dias_vacaciones_tomados)


class Asistencia(models.Model):
    empleado = models.ForeignKey(Empleado, on_delete=models.CASCADE, related_name='asistencias')
    fecha = models.DateField(default=timezone.localdate)
    hora_entrada = models.TimeField(default=timezone.localtime)
    hora_salida = models.TimeField(null=True, blank=True)
    justificacion_correccion = models.TextField(blank=True)

    def __str__(self):
        return f"{self.empleado} - {self.fecha}"

    @property
    def horas_trabajadas(self):
        if not self.hora_salida:
            return 0.0
        dt_in = datetime.combine(self.fecha, self.hora_entrada)
        dt_out = datetime.combine(self.fecha, self.hora_salida)
        if dt_out <= dt_in:
            return 0.0
        return round((dt_out - dt_in).total_seconds() / 3600, 2)

    @property
    def horas_extras(self):
        return round(max(0.0, self.horas_trabajadas - 8.0), 2)


class Permiso(models.Model):
    TIPOS = [
        ('personal', 'Personal'),
        ('médico', 'Médico'),
        ('duelo', 'Duelo'),
        ('maternidad/paternidad', 'Maternidad/Paternidad'),
        ('otro', 'Otro'),
    ]
    ESTADOS = [
        ('pendiente', 'Pendiente'),
        ('aprobado', 'Aprobado'),
        ('rechazado', 'Rechazado'),
    ]
    empleado = models.ForeignKey(Empleado, on_delete=models.CASCADE, related_name='permisos')
    tipo = models.CharField(max_length=25, choices=TIPOS)
    fecha_inicio = models.DateField()
    fecha_fin = models.DateField()
    motivo = models.TextField()
    adjunto_descripcion = models.CharField(max_length=255, blank=True)
    estado = models.CharField(max_length=15, choices=ESTADOS, default='pendiente')

    def __str__(self):
        return f"{self.empleado} ({self.tipo} - {self.estado})"