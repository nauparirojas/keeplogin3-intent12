import logging
from django.contrib.auth import logout
from django.utils import timezone
from .models import Asistencia

logger = logging.getLogger('asistencia_auditoria')


class ControlAsistenciaMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def _obtener_ip(self, request):
        forwarded = request.META.get('HTTP_X_FORWARDED_FOR')
        if forwarded:
            return forwarded.split(',')[0].strip()
        return request.META.get('REMOTE_ADDR')

    def __call__(self, request):
        if request.user.is_authenticated and not request.user.is_active:
            logout(request)

        if request.user.is_authenticated and not request.session.get('aviso_asistencia_hoy'):
            hoy = timezone.localdate()
            if hoy.weekday() < 5:
                tiene_entrada = Asistencia.objects.filter(
                    empleado__usuario=request.user,
                    fecha=hoy,
                ).exists()
                if not tiene_entrada:
                    request.session['alerta_asistencia'] = 'Recuerda registrar tu marcación de asistencia de hoy.'
            request.session['aviso_asistencia_hoy'] = True

        response = self.get_response(request)

        usuario = request.user.username if request.user.is_authenticated else 'anonimo'
        ip = self._obtener_ip(request)

        if response.status_code in (401, 403):
            logger.warning(
                f"ASISTENCIA_DENEGADO | status={response.status_code} | user={usuario} | ip={ip} | method={request.method} | path={request.path}"
            )
        elif request.method in ('POST', 'PUT', 'PATCH', 'DELETE'):
            logger.info(
                f"ASISTENCIA_AUDIT | user={usuario} | ip={ip} | method={request.method} | path={request.path}"
            )

        return response