from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render
from .forms import MarcacionAsistenciaForm, PermisoForm
from .models import Asistencia, Empleado, Permiso


def _es_admin_rrhh(user):
    return user.is_superuser or user.groups.filter(name='Admin RRHH').exists()


def _es_jefe_area(user):
    return user.groups.filter(name='Jefe de Área').exists()


@login_required
def panel_asistencia_view(request):
    alerta = request.session.pop('alerta_asistencia', None)
    asistencias_qs = Asistencia.objects.select_related('empleado', 'empleado__area').order_by('-fecha', '-hora_entrada')
    permisos_qs = Permiso.objects.select_related('empleado', 'empleado__area').order_by('-fecha_inicio')

    if not _es_admin_rrhh(request.user) and not request.user.groups.filter(name='Contador').exists():
        empleado_actual = Empleado.objects.select_related('area').filter(usuario=request.user).first()
        if empleado_actual:
            if _es_jefe_area(request.user):
                asistencias_qs = asistencias_qs.filter(empleado__area=empleado_actual.area)
                permisos_qs = permisos_qs.filter(empleado__area=empleado_actual.area)
            else:
                asistencias_qs = asistencias_qs.filter(empleado=empleado_actual)
                permisos_qs = permisos_qs.filter(empleado=empleado_actual)

    return render(
        request,
        'asistencia/panel.html',
        {
            'asistencias': asistencias_qs,
            'permisos': permisos_qs,
            'alerta': alerta,
            'es_admin_rrhh': _es_admin_rrhh(request.user),
            'es_jefe_area': _es_jefe_area(request.user),
        },
    )


@login_required
@permission_required('asistencia.add_asistencia', raise_exception=True)
def marcar_asistencia_view(request):
    if request.method == 'POST':
        form = MarcacionAsistenciaForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Asistencia registrada correctamente.')
            return redirect('panel_asistencia')
    else:
        form = MarcacionAsistenciaForm()
    return render(request, 'asistencia/form.html', {'form': form, 'titulo': 'Marcar Asistencia'})


@login_required
@permission_required('asistencia.add_permiso', raise_exception=True)
def solicitar_permiso_view(request):
    if request.method == 'POST':
        form = PermisoForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Solicitud de permiso registrada en estado pendiente.')
            return redirect('panel_asistencia')
    else:
        form = PermisoForm()
    return render(request, 'asistencia/form.html', {'form': form, 'titulo': 'Solicitar Permiso'})


@login_required
@permission_required('asistencia.change_permiso', raise_exception=True)
def aprobar_permiso_view(request, permiso_id):
    if request.method != 'POST':
        return redirect('panel_asistencia')

    permiso = get_object_or_404(Permiso.objects.select_related('empleado', 'empleado__area'), pk=permiso_id)

    if not _es_admin_rrhh(request.user):
        if not _es_jefe_area(request.user):
            raise PermissionDenied('No tienes permiso para aprobar solicitudes.')
        emp_jefe = Empleado.objects.select_related('area').filter(usuario=request.user).first()
        if not emp_jefe or emp_jefe.area_id != permiso.empleado.area_id:
            raise PermissionDenied('Solo puedes aprobar permisos de empleados de tu propia área.')

    if permiso.estado == 'aprobado':
        messages.info(request, 'Este permiso ya estaba aprobado.')
        return redirect('panel_asistencia')

    dias = (permiso.fecha_fin - permiso.fecha_inicio).days + 1
    with transaction.atomic():
        emp = Empleado.objects.select_for_update().get(pk=permiso.empleado_id)
        if dias > emp.dias_vacaciones_disponibles:
            messages.error(request, 'El empleado no cuenta con días de vacaciones suficientes.')
            return redirect('panel_asistencia')
        permiso.estado = 'aprobado'
        permiso.save(update_fields=['estado'])
        emp.dias_vacaciones_tomados += dias
        emp.save(update_fields=['dias_vacaciones_tomados'])

    messages.success(request, f'Permiso de {permiso.empleado} aprobado ({dias} día(s) descontados).')
    return redirect('panel_asistencia')