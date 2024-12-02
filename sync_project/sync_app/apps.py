from django.apps import AppConfig
from django.conf import settings
import os

class SyncAppConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'sync_app'

    def ready(self):
        if os.environ.get('RUN_MAIN', None) != 'true':
            # Запускаємо планувальник тільки в основному процесі
            return

        from .jobs import start_scheduler
        try:
            start_scheduler()
        except Exception as e:
            import logging
            logging.error(f"Error starting scheduler: {e}")