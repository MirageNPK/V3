import logging
from .models import NotionDbConfig
from .notion_connector import NotionConnector, NotionServiceReportConnector, NotionResponsibleReportConnector, NotionBuReportConnector

logger = logging.getLogger(__name__)

def sync_notion_orders():
    configs = NotionDbConfig.objects.filter(is_active=True,database_id_from="13e3a17e5d7f80da9a55e1a01feda7b3")
    if not configs.exists():
        logger.error("No active NotionDbConfig records found.")
        print("❌ No active configurations.")
        return

    for config in configs:
        logger.info(f"Processing NotionDbConfig: {config.name}")
        print(f"🔄 Syncing orders data from database: {config.database_id_from}")

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
    configs = NotionDbConfig.objects.filter(is_active=True, database_id_to="1733a17e5d7f8009bbf6d7c68b1cacf1")
    if not configs.exists():
        logger.error("No active NotionDbConfig records found.")
        print("❌ No active configurations.")
        return

    for config in configs:
        logger.info(f"Processing NotionDbConfig: {config.name}")
        print(f"🔄 Syncing services data to database: {config.database_id_to}")

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

def sync_notion_responsible_report():
    configs = NotionDbConfig.objects.filter(is_active=True, database_id_to="1743a17e5d7f80daa1e2c6c5c7cc979c")
    if not configs.exists():
        logger.error("No active NotionDbConfig records found.")
        print("❌ No active configurations.")
        return

    for config in configs:
        logger.info(f"Processing NotionDbConfig: {config.name}")
        print(f"🔄 Syncing responsible data to database: {config.database_id_to}")

        try:
            connector = NotionResponsibleReportConnector(
                notion_token=config.notion_token,
                database_id=config.database_id_to
            )
            result = connector.sync_service_report()
            logger.info(f"✅ Sync result for {config.database_id_to}: {result}")
            print(f"✅ {result}")
        except Exception as e:
            logger.error(f"Error syncing database {config.database_id_to}: {str(e)}")
            print(f"❌ Error: {str(e)}")

def sync_notion_bunit_report():
    configs = NotionDbConfig.objects.filter(is_active=True, database_id_to="1743a17e5d7f801b8009d5b5788e8c00")
    if not configs.exists():
        logger.error("No active NotionDbConfig records found.")
        print("❌ No active configurations.")
        return

    for config in configs:
        logger.info(f"Processing NotionDbConfig: {config.name}")
        print(f"🔄 Syncing bunit data to database: {config.database_id_to}")

        try:
            connector = NotionBuReportConnector(
                notion_token=config.notion_token,
                database_id=config.database_id_to
            )
            result = connector.sync_service_report()
            logger.info(f"✅ Sync result for {config.database_id_to}: {result}")
            print(f"✅ {result}")
        except Exception as e:
            logger.error(f"Error syncing database {config.database_id_to}: {str(e)}")
            print(f"❌ Error: {str(e)}")