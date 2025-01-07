import logging
from django.core.management.base import BaseCommand
from nontion_sync.tasks import sync_notion_orders

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = "Sync data from Notion orders database"

    def handle(self, *args, **kwargs):
        self.stdout.write("🚀 Starting Notion Orders Sync...")
        try:
            sync_notion_orders()
            self.stdout.write("✅ Sync completed successfully.")
        except Exception as e:
            logger.error(f"Critical error during Notion Orders Sync: {str(e)}")
            self.stdout.write(f"❌ Error: {str(e)}")

