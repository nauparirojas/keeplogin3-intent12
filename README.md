# Caso 3: Control de Asistencia y Permisos (TecnoAndes S.A.C.)

Aplicación Django independiente para el **Caso 3** de la Práctica Grupal Semana 12 (IS093A):
- Gestión de empleados y áreas (`Sistemas`, `Contabilidad`, `Ventas`, `Logística`, `RRHH`) con validación de correo `@tecnoandes.pe`, fecha de ingreso no futura y cálculo de antigüedad.
- Marcación de asistencia con prevención de entradas abiertas duplicadas, cálculo de horas trabajadas y horas extras (>8h), y solicitud de permisos con validación de fechas, solapamiento y vacaciones disponibles (30 días base).
- Middleware de control y auditoría, sesión con timeout de 45 minutos y Django Admin operativo.

## Ejecución
1. `python -m venv venv` y `.\venv\Scripts\Activate`
2. `pip install -r requirements.txt`
3. `python manage.py makemigrations` y `python manage.py migrate`
4. `python manage.py createsuperuser` y `python manage.py runserver`
