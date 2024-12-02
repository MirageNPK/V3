import traceback
import logging
from .notion_connector import NotionConnector
from .models import NotionConfig

def bu_projects():
    try:
        print("🔹 Starting Notion sync process...")

        # Фільтрація записів за database_id
        configs = NotionConfig.objects.filter(database_id="1413a17e5d7f80dfb1b3d509a3f9318e")
        if not configs.exists():
            logging.error("No matching NotionConfig records found.")
            print("❌ No matching NotionConfig records found.")
            return

        for config in configs:
            print("\n🔄 Processing configuration:")
            print(f"📌 Notion Token: {'*' * 10}{config.notion_token[-5:]}")
            print(f"📌 Database ID: {config.database_id}")
            print(f"📌 Auth Endpoint: {config.auth_endpoint}")
            print(f"📌 Data Endpoint: {config.data_endpoint}")

            try:
                # Ініціалізація конектора
                connector = NotionConnector(
                    notion_token=config.notion_token,
                    database_id=config.database_id,
                    auth_endpoint=config.auth_endpoint,
                    data_endpoint=config.data_endpoint
                )

                # Виклик основного методу синхронізації
                result = connector.sync_data(config.api_login, config.api_password)

                print(f"✅ Sync for {config.database_id} completed with result: {result}")
            except Exception as sync_error:
                print(f"❌ Sync failed for {config.database_id}")
                print(traceback.format_exc())
                logging.error(f"Sync error for {config.database_id}: {str(sync_error)}")
                logging.error(traceback.format_exc())

    except Exception as e:
        print("❌ Critical error occurred during sync process:")
        print(traceback.format_exc())
        logging.error(f"Critical sync error: {str(e)}")
        logging.error(traceback.format_exc())

if __name__ == "__bu_projects__":
    bu_projects()
