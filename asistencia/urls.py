from django.urls import path
from . import views

urlpatterns = [
    path('', views.panel_asistencia_view, name='panel_asistencia'),
    path('marcar/', views.marcar_asistencia_view, name='marcar_asistencia'),
    path('permisos/nuevo/', views.solicitar_permiso_view, name='permiso_nuevo'),
    path('permisos/<int:permiso_id>/aprobar/', views.aprobar_permiso_view, name='permiso_aprobar'),
]