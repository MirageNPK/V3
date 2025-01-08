from django_apscheduler.jobstores import DjangoJobStore
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
import logging
from django.core.management import call_command

logger = logging.getLogger(__name__)

def start_sync_job():
    try:
        call_command('start_notion_sync')
        logger.info("Sync job executed successfully.")
    except Exception as e:
        logger.error(f"Error executing sync job: {e}")
def sync_notion_order():
    scheduler = BackgroundScheduler()
    scheduler.add_jobstore(DjangoJobStore(), "default")
    scheduler.add_job(
        start_sync_job,
        trigger=IntervalTrigger(minutes=5),  # Інтервал синхронізації
        id="sync_notion_orders",
        replace_existing=True,
    )

    scheduler.start()
    logger.info("Notion sync scheduler started.")
