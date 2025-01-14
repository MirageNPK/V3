# from django.apps import AppConfig
# import logging
# import os
# logger = logging.getLogger(__name__)

# class MainConfig(AppConfig):
#     default_auto_field = 'django.db.models.BigAutoField'
#     name = 'nontion_sync'

#     def ready(self):
#         if os.environ.get("RUN_MAIN", None) == "true":
#             from .jobs import sync_notion_order
#             logger.info("Initializing the scheduler...")
#             # sync_notion_order()