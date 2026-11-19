from django.contrib import admin
from django.http import HttpResponse
from django.urls import path
from django.utils.html import format_html
from .models import Area, Asistencia, Empleado, Permiso


@admin.register(Area)
class AreaAdmin(admin.ModelAdmin):
    list_display = ('nombre',)
    search_fields = ('nombre',)


@admin.register(Empleado)
class EmpleadoAdmin(admin.ModelAdmin):
    list_display = (
        'dni', 'apellidos', 'nombres', 'area', 'cargo',
        'tipo_contrato', 'antiguedad_texto', 'dias_vacaciones_disponibles'
    )
    list_filter = ('area', 'tipo_contrato')
    search_fields = ('dni', 'nombres', 'apellidos', 'email_corporativo')
    list_select_related = ('area',)


@admin.register(Asistencia)
class AsistenciaAdmin(admin.ModelAdmin):
    list_display = ('empleado', 'fecha', 'hora_entrada', 'hora_salida', 'horas_trabajadas', 'horas_extras')
    list_filter = ('fecha', 'empleado__area')
    search_fields = ('empleado__dni', 'empleado__apellidos', 'empleado__nombres')
    list_select_related = ('empleado', 'empleado__area')
    actions = ['exportar_reporte_txt']

    def changelist_view(self, request, extra_context=None):
        extra_context = extra_context or {}
        extra_context['reporte_link'] = format_html(
            '<a class="button" href="{}">Reporte de Horas Extras</a>',
            'reporte-extras/',
        )
        return super().changelist_view(request, extra_context=extra_context)

    def get_urls(self):
        urls = super().get_urls()
        custom = [
            path(
                'reporte-extras/',
                self.admin_site.admin_view(self.reporte_extras_view),
                name='asistencia_reporte_extras',
            ),
        ]
        return custom + urls

    def reporte_extras_view(self, request):
        empleados = Empleado.objects.select_related('area').prefetch_related('asistencias').order_by('area__nombre', 'apellidos')
        lineas = ['REPORTE DE HORAS EXTRAS POR EMPLEADO', '=' * 50]
        for emp in empleados:
            total_extras = round(sum(a.horas_extras for a in emp.asistencias.all()), 2)
            lineas.append(f"{emp.dni} | {emp} | Cargo: {emp.cargo} | Extras acumuladas: {total_extras} h")
        return HttpResponse('\n'.join(lineas), content_type='text/plain; charset=utf-8')

    @admin.action(description='Exportar asistencias seleccionadas (.txt)')
    def exportar_reporte_txt(self, request, queryset):
        registros = queryset.select_related('empleado', 'empleado__area')
        lineas = [
            f"{a.fecha} | {a.empleado} | In:{a.hora_entrada} | Out:{a.hora_salida or '-'} | Horas:{a.horas_trabajadas}h | Extras:{a.horas_extras}h"
            for a in registros
        ]
        return HttpResponse('\n'.join(lineas), content_type='text/plain; charset=utf-8')


@admin.register(Permiso)
class PermisoAdmin(admin.ModelAdmin):
    list_display = ('empleado', 'tipo', 'fecha_inicio', 'fecha_fin', 'estado')
    list_filter = ('estado', 'tipo', 'fecha_inicio', 'empleado__area')
    search_fields = ('empleado__apellidos', 'empleado__nombres', 'motivo')
    list_select_related = ('empleado', 'empleado__area')
    actions = ['aprobar_permisos']

    @admin.action(description='Aprobar permisos seleccionados')
    def aprobar_permisos(self, request, queryset):
        aprobados = 0
        for permiso in queryset.select_related('empleado'):
            if permiso.estado != 'aprobado':
                dias = (permiso.fecha_fin - permiso.fecha_inicio).days + 1
                permiso.estado = 'aprobado'
                permiso.save(update_fields=['estado'])
                permiso.empleado.dias_vacaciones_tomados += dias
                permiso.empleado.save(update_fields=['dias_vacaciones_tomados'])
                aprobados += 1
        self.message_user(request, f"{aprobados} permiso(s) aprobado(s) y días descontados.")