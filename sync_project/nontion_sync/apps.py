from django.apps import AppConfig
from django.conf import settings
import os

class SyncAppConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'nontion_sync'

    def ready(self):
        if os.environ.get('RUN_MAIN', None) != 'true':
            # Запускаємо планувальник тільки в основному процесі
            return

        from .jobs import  sync_service_report_job
        try:
            
            sync_service_report_job()
        except Exception as e:
            import logging
            logging.error(f"Error starting scheduler: {e}")
