import logging
from .models import NotionDbConfig
from .notion_connector import NotionConnector, NotionServiceReportConnector

logger = logging.getLogger(__name__)

def sync_notion_orders():
    configs = NotionDbConfig.objects.filter(is_active=True)
    if not configs.exists():
        logger.error("No active NotionDbConfig records found.")
        print("❌ No active configurations.")
        return

    for config in configs:
        logger.info(f"Processing NotionDbConfig: {config.name}")
        print(f"🔄 Syncing data from database: {config.database_id_from}")

        try:
            connector = NotionConnector(
                notion_token=config.notion_token,
                database_id=config.database_id_from
            )
            result = connector.sync_orders()
            logger.info(f"✅ Sync result for {config.database_id_from}: {result}")
            print(f"✅ {result}")
        except Exception as e:
            logger.error(f"Error syncing database {config.database_id_from}: {str(e)}")
            print(f"❌ Error: {str(e)}")

def sync_notion_service_report():
    configs = NotionDbConfig.objects.filter(is_active=True)
    if not configs.exists():
        logger.error("No active NotionDbConfig records found.")
        print("❌ No active configurations.")
        return

    for config in configs:
        logger.info(f"Processing NotionDbConfig: {config.name}")
        print(f"🔄 Syncing data to database: {config.database_id_to}")

        try:
            connector = NotionServiceReportConnector(
                notion_token=config.notion_token,
                database_id=config.database_id_to
            )
            result = connector.sync_service_report()
            logger.info(f"✅ Sync result for {config.database_id_to}: {result}")
            print(f"✅ {result}")
        except Exception as e:
            logger.error(f"Error syncing database {config.database_id_to}: {str(e)}")
            print(f"❌ Error: {str(e)}")