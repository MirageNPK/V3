from django_apscheduler.jobstores import DjangoJobStore
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from django.core.management import call_command
import logging

logger = logging.getLogger(__name__)

def start_sync_job():
    try:
        call_command('start_sync')
        logger.info("Sync job executed successfully.")
    except Exception as e:
        logger.error(f"Error executing sync job: {e}")

def start_scheduler():
    scheduler = BackgroundScheduler()
    scheduler.add_jobstore(DjangoJobStore(), "default")
    scheduler.add_job(
        start_sync_job,
        trigger=IntervalTrigger(minutes=155),
        id="sync_job",
        replace_existing=True,
    )
    scheduler.start()
    logger.info("Scheduler started.")