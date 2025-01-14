from __future__ import absolute_import, unicode_literals
import os
from celery import Celery

# Вказуємо стандартне значення для налаштувань Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sync_project.settings')

# Створюємо об'єкт Celery
app = Celery('sync_project')

# Читаємо конфігурацію з налаштувань Django
app.config_from_object('django.conf:settings', namespace='CELERY')

# Автоматичне виявлення тасок у всіх встановлених додатках
app.autodiscover_tasks(['nontion_sync', 'sync_app'])

@app.task(bind=True)
def debug_task(self):
    print(f'Request: {self.request!r}')
