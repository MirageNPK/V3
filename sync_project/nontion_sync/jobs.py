from django_apscheduler.jobstores import DjangoJobStore
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
import logging
from .management.commands import  start_notion_sync

logger = logging.getLogger(__name__)

# def sync_notion_order():
#     scheduler = BackgroundScheduler()
#     scheduler.add_jobstore(DjangoJobStore(), "default")

#     scheduler.add_job(
#         sync_notion_orders,
#         trigger=IntervalTrigger(minutes=5),  # Інтервал синхронізації
#         id="notion_sync_job",
#         replace_existing=True,
#     )

#     scheduler.start()
#     logger.info("Notion sync scheduler started.")

def sync_service_report_job():
    scheduler = BackgroundScheduler()
    scheduler.add_jobstore(DjangoJobStore(), "default")

    scheduler.add_job(
        start_notion_sync,
        trigger=IntervalTrigger(minutes=5),  # Інтервал виконання
        id="notion_sync_service_report_job",
        replace_existing=True,
    )

    scheduler.start()
    logger.info("Service report sync job started.")