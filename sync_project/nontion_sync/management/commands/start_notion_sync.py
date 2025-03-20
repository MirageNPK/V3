import logging
from django.core.management.base import BaseCommand
from nontion_sync.tasks import sync_notion_workload, sync_notion_service_report, sync_notion_orders, sync_notion_responsible_report, sync_notion_bunit_report, sync_notion_workloadtemporary, sync_notion_projects, sync_notion_tasks
from AI_assistants.tasks import send_task_reminders
logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = "Sync service data from the database to Notion table"

    def handle(self, *args, **kwargs):
        self.stdout.write("🚀 Starting Service Report Sync...")
        try:
            sync_notion_orders()
            # sync_notion_tasks()
            # sync_notion_service_report()
            # sync_notion_responsible_report()
            # sync_notion_bunit_report()
            # sync_notion_workload ()
            # sync_notion_projects()
            # sync_notion_workloadtemporary()
            # send_task_reminders()
            self.stdout.write("✅ Sync completed successfully.")
        except Exception as e:
            logger.error(f"Critical error during Service Report Sync: {str(e)}")
            self.stdout.write(f"❌ Error: {str(e)}") 