import time
import logging
from notion_client import Client
from .models import NotionOrders
from django.db.models import Sum, F,Q
from datetime import datetime
from django.db.models.functions import ExtractMonth
from hashlib import md5
import os
import sys
# logger = logging.getLogger(__name__)
# Створюємо директорію для логів, якщо її ще немає
log_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'logs')
os.makedirs(log_dir, exist_ok=True)

# Шлях до файлу логів
log_file = os.path.join(log_dir, 'notion_sync.log')

# Конфігурація логування
logging.basicConfig(
    filename=os.path.join(log_dir, 'notion_sync.log'),
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    encoding="utf-8",  # Додаємо кодування
)

logger = logging.getLogger("notion_sync")


#  формування звіту по Виконавцям ордерів       
class NotionResponsibleReportConnector:
    def __init__(self, notion_token, database_id):
        self.notion = Client(auth=notion_token)
        self.database_id = database_id
        
    def sync_service_report(self):
        retries = 3
        timeout = 5
        records_synced = 0

        for attempt in range(1, retries + 1):
            try:
                # Групуємо дані за responsible і підраховуємо значення для кожного місяця
                responsible_data = (
                    NotionOrders.objects
                    .values('responsible')  # Групуємо за "responsible"
                    .annotate(
                        jan=Sum('order_cost', filter=Q(finish_date__month=1)),
                        feb=Sum('order_cost', filter=Q(finish_date__month=2)),
                        mar=Sum('order_cost', filter=Q(finish_date__month=3)),
                        apr=Sum('order_cost', filter=Q(finish_date__month=4)),
                        may=Sum('order_cost', filter=Q(finish_date__month=5)),
                        jun=Sum('order_cost', filter=Q(finish_date__month=6)),
                        jul=Sum('order_cost', filter=Q(finish_date__month=7)),
                        aug=Sum('order_cost', filter=Q(finish_date__month=8)),
                        sep=Sum('order_cost', filter=Q(finish_date__month=9)),
                        oct=Sum('order_cost', filter=Q(finish_date__month=10)),
                        nov=Sum('order_cost', filter=Q(finish_date__month=11)),
                        dec=Sum('order_cost', filter=Q(finish_date__month=12)),
                    )
                )

                 # Отримуємо існуючі записи з Notion
                query_response = self.notion.databases.query(
                    database_id=self.database_id,
                )
                notion_pages = query_response.get("results", [])

                # Створюємо набір всіх service_id, які зараз є в базі Notion
                notion_service_ids = {page['properties']['Responsible Name']['title'][0]['text']['content'] for page in notion_pages}

                # Створення нових або оновлення записів, також видалення непотрібних
                for res in responsible_data:
                    notion_data = self._prepare_service_data(res)
                    self._update_or_create_record(res['responsible'], notion_data)
                    records_synced += 1
                    # Видалення з Notion, якщо запису немає в нових даних
                    notion_service_ids.discard(str(res['responsible']))

                # Видаляємо з Notion сервіси, яких немає в нових даних
                for service_id_to_remove in notion_service_ids:
                    self._delete_record_from_notion(service_id_to_remove)

                logger.info(f"✅ Successfully synced {records_synced} records.")
                break  # Виходимо з циклу, якщо успішно

            except Exception as e:
                logger.error(f"Attempt {attempt} failed: {str(e)}. Retrying in {timeout} seconds...")
                time.sleep(timeout)
                timeout *= 2

        return f"Sync completed. {records_synced} records synced."

    def _prepare_service_data(self, service):
        """Підготовка даних для передачі в Notion."""
        # Витягуємо значення для кожного місяця
        month_columns = {
            "1.25": service.get('jan', 0) or 0,
            "2.25": service.get('feb', 0) or 0,
            "3.25": service.get('mar', 0) or 0,
            "4.25": service.get('apr', 0) or 0,
            "5.25": service.get('may', 0) or 0,
            "6.25": service.get('jun', 0) or 0,
            "7.25": service.get('jul', 0) or 0,
            "8.25": service.get('aug', 0) or 0,
            "9.25": service.get('sep', 0) or 0,
            "10.25": service.get('oct', 0) or 0,
            "11.25": service.get('nov', 0) or 0,
            "12.25": service.get('dec', 0) or 0,
        }

        return {
            "Responsible Name": {
                "title": [{"type": "text", "text": {"content": service['responsible']}}]
            },
            **{key: {"number": float(value)} for key, value in month_columns.items()},
        }

    def _update_or_create_record(self, responsible, data):
        """Оновлює або створює запис у базі Notion."""
        # Отримуємо наявні сторінки в Notion
        query_response = self.notion.databases.query(
            database_id=self.database_id,
            filter={"property": "Responsible Name", "title": {"equals": responsible}}
        )
        pages = query_response.get("results", [])

        if pages:
            # Оновлюємо існуючий запис
            page_id = pages[0]['id']
            self.notion.pages.update(page_id=page_id, properties=data)
            logger.info(f"Updated record with responsible: {responsible}")
        else:
            # Створюємо новий запис
            self.notion.pages.create(parent={"database_id": self.database_id}, properties=data)
            logger.info(f"Created new record with responsible: {responsible}")

    def _delete_record_from_notion(self, responsible):
        """Архівує запис з бази Notion"""
        query_response = self.notion.databases.query(
            database_id=self.database_id,
            filter={"property": "Responsible Name", "rich_text": {"equals": str(responsible)}}
        )
        
        pages = query_response.get("results", [])
        
        if pages:
            for page in pages:
                page_id = page['id']
                try:
                    # Архівуємо сторінку 
                    self.notion.pages.update(page_id=page_id, archived=True)
                    logger.info(f"Archived record with service_id: {responsible} and page_id: {page_id}")
                except Exception as e:
                    logger.error(f"Failed to archive page with service_id: {responsible}. Error: {str(e)}")
        else:
            logger.warning(f"No page found for service_id: {responsible}")

# Формування звіту по бізнесюнітам які роблять замовлення
class NotionBuReportConnector:
    def __init__(self, notion_token, database_id):
        self.notion = Client(auth=notion_token)
        self.database_id = database_id

    def sync_service_report(self):
        retries = 3
        timeout = 5
        records_synced = 0

        for attempt in range(1, retries + 1):
            try:
                # Групуємо дані за business_unit_id і підраховуємо значення для кожного місяця
                business_unit_data = (
                    NotionOrders.objects
                    .values('business_unit_id', 'business_unit' )  # Групуємо за "business_unit_id"
                    .annotate(
                        jan=Sum('order_cost', filter=Q(finish_date__month=1)),
                        feb=Sum('order_cost', filter=Q(finish_date__month=2)),
                        mar=Sum('order_cost', filter=Q(finish_date__month=3)),
                        apr=Sum('order_cost', filter=Q(finish_date__month=4)),
                        may=Sum('order_cost', filter=Q(finish_date__month=5)),
                        jun=Sum('order_cost', filter=Q(finish_date__month=6)),
                        jul=Sum('order_cost', filter=Q(finish_date__month=7)),
                        aug=Sum('order_cost', filter=Q(finish_date__month=8)),
                        sep=Sum('order_cost', filter=Q(finish_date__month=9)),
                        oct=Sum('order_cost', filter=Q(finish_date__month=10)),
                        nov=Sum('order_cost', filter=Q(finish_date__month=11)),
                        dec=Sum('order_cost', filter=Q(finish_date__month=12)),
                    )
                )

                # Отримуємо існуючі записи з Notion
                query_response = self.notion.databases.query(
                    database_id=self.database_id,
                )
                notion_pages = query_response.get("results", [])

                # Створюємо набір всіх service_id, які зараз є в базі Notion
                notion_service_ids = {page['properties']['BU ID']['rich_text'][0]['text']['content'] for page in notion_pages}

                # Створення нових або оновлення записів, також видалення непотрібних
                for res in business_unit_data:
                    notion_data = self._prepare_service_data(res)
                    self._update_or_create_record(res['business_unit_id'], notion_data)
                    records_synced += 1
                    # Видалення з Notion, якщо запису немає в нових даних
                    notion_service_ids.discard(str(res['business_unit_id']))

                # Видаляємо з Notion сервіси, яких немає в нових даних
                for service_id_to_remove in notion_service_ids:
                    self._delete_record_from_notion(service_id_to_remove)

                logger.info(f"✅ Successfully synced {records_synced} records.")
                break  # Виходимо з циклу, якщо успішно

            except Exception as e:
                logger.error(f"Attempt {attempt} failed: {str(e)}. Retrying in {timeout} seconds...")
                time.sleep(timeout)
                timeout *= 2

        return f"Sync completed. {records_synced} records synced."

    def _prepare_service_data(self, service):
        """Підготовка даних для передачі в Notion."""
        # Витягуємо значення для кожного місяця
        month_columns = {
            "1.25": service.get('jan', 0) or 0,
            "2.25": service.get('feb', 0) or 0,
            "3.25": service.get('mar', 0) or 0,
            "4.25": service.get('apr', 0) or 0,
            "5.25": service.get('may', 0) or 0,
            "6.25": service.get('jun', 0) or 0,
            "7.25": service.get('jul', 0) or 0,
            "8.25": service.get('aug', 0) or 0,
            "9.25": service.get('sep', 0) or 0,
            "10.25": service.get('oct', 0) or 0,
            "11.25": service.get('nov', 0) or 0,
            "12.25": service.get('dec', 0) or 0,
        }

        return {
            "BU Name": {
                "title": [{"type": "text", "text": {"content": service['business_unit']}}]
            },
            **{key: {"number": float(value)} for key, value in month_columns.items()},
        }

    def _update_or_create_record(self, business_unit_id, data):
        """Оновлює або створює запис у базі Notion."""
        # Отримуємо наявні сторінки в Notion
        query_response = self.notion.databases.query(
            database_id=self.database_id,
            filter={"property": "BU ID", "rich_text": {"equals": str(business_unit_id)}}
        )
        pages = query_response.get("results", [])

        if pages:
            # Оновлюємо існуючий запис
            page_id = pages[0]['id']
            self.notion.pages.update(page_id=page_id, properties=data)
            logger.info(f"Updated record with responsible: {business_unit_id}")
        else:
            # Створюємо новий запис
            self.notion.pages.create(parent={"database_id": self.database_id}, properties=data)
            logger.info(f"Created new record with responsible: {business_unit_id}")
    
    def _delete_record_from_notion(self, business_unit_id):
        """Архівує запис з бази Notion"""
        query_response = self.notion.databases.query(
            database_id=self.database_id,
            filter={"property": "BU ID", "rich_text": {"equals": str(business_unit_id)}}
        )
        
        pages = query_response.get("results", [])
        
        if pages:
            for page in pages:
                page_id = page['id']
                try:
                    # Архівуємо сторінку 
                    self.notion.pages.update(page_id=page_id, archived=True)
                    logger.info(f"Archived record with service_id: {business_unit_id} and page_id: {page_id}")
                except Exception as e:
                    logger.error(f"Failed to archive page with service_id: {business_unit_id}. Error: {str(e)}")
        else:
            logger.warning(f"No page found for service_id: {business_unit_id}")

# Формування звіту по послугам наданим в ордерах
class NotionServiceReportConnector:
    def __init__(self, notion_token, database_id):
        self.notion = Client(auth=notion_token)
        self.database_id = database_id

    def sync_service_report(self):
        retries = 3
        timeout = 5
        records_synced = 0

        for attempt in range(1, retries + 1):
            try:
                # Отримуємо актуальні дані з бази
                service_data = (
                    NotionOrders.objects
                    .values('service_id', 'service_name')  # Групуємо за "service_id"
                    .annotate(
                        jan=Sum('order_cost', filter=Q(finish_date__month=1)),
                        feb=Sum('order_cost', filter=Q(finish_date__month=2)),
                        mar=Sum('order_cost', filter=Q(finish_date__month=3)),
                        apr=Sum('order_cost', filter=Q(finish_date__month=4)),
                        may=Sum('order_cost', filter=Q(finish_date__month=5)),
                        jun=Sum('order_cost', filter=Q(finish_date__month=6)),
                        jul=Sum('order_cost', filter=Q(finish_date__month=7)),
                        aug=Sum('order_cost', filter=Q(finish_date__month=8)),
                        sep=Sum('order_cost', filter=Q(finish_date__month=9)),
                        oct=Sum('order_cost', filter=Q(finish_date__month=10)),
                        nov=Sum('order_cost', filter=Q(finish_date__month=11)),
                        dec=Sum('order_cost', filter=Q(finish_date__month=12)),
                    )
                )

                # Отримуємо існуючі записи з Notion
                query_response = self.notion.databases.query(
                    database_id=self.database_id,
                )
                notion_pages = query_response.get("results", [])

                # Створюємо набір всіх service_id, які зараз є в базі Notion
                notion_service_ids = {page['properties']['ID Service']['rich_text'][0]['text']['content'] for page in notion_pages}

                # Створення нових або оновлення записів, також видалення непотрібних
                for res in service_data:
                    notion_data = self._prepare_service_data(res)
                    self._update_or_create_record(res['service_id'], notion_data)
                    records_synced += 1
                    # Видалення з Notion, якщо запису немає в нових даних
                    notion_service_ids.discard(str(res['service_id']))

                # Видаляємо з Notion сервіси, яких немає в нових даних
                for service_id_to_remove in notion_service_ids:
                    self._delete_record_from_notion(service_id_to_remove)

                logger.info(f"✅ Successfully synced {records_synced} records.")
                break  # Виходимо з циклу, якщо успішно

            except Exception as e:
                logger.error(f"Attempt {attempt} failed: {str(e)}. Retrying in {timeout} seconds...")
                time.sleep(timeout)
                timeout *= 2

        return f"Sync completed. {records_synced} records synced."

    def _prepare_service_data(self, service):
        """Підготовка даних для передачі в Notion."""
        service_id = service['service_id']

        # Підготовка даних для місяців
        month_columns = {
            "1.25": service.get('jan', 0) or 0,
            "2.25": service.get('feb', 0) or 0,
            "3.25": service.get('mar', 0) or 0,
            "4.25": service.get('apr', 0) or 0,
            "5.25": service.get('may', 0) or 0,
            "6.25": service.get('jun', 0) or 0,
            "7.25": service.get('jul', 0) or 0,
            "8.25": service.get('aug', 0) or 0,
            "9.25": service.get('sep', 0) or 0,
            "10.25": service.get('oct', 0) or 0,
            "11.25": service.get('nov', 0) or 0,
            "12.25": service.get('dec', 0) or 0,
        }

        return {
            "ID Service": {
                "rich_text": [{"text": {"content": str(service_id)}}]
            },
            "Service Name": {
                "title": [{"type": "text", "text": {"content": service['service_name']}}]
            },
            **{key: {"number": float(value)} for key, value in month_columns.items()},
        }

    def _update_or_create_record(self, service_id, data):
        """Оновлює або створює запис у базі Notion."""
        query_response = self.notion.databases.query(
            database_id=self.database_id,
            filter={"property": "ID Service", "rich_text": {"equals": str(service_id)}}
        )
        pages = query_response.get("results", [])

        if pages:
            page_id = pages[0]['id']
            self.notion.pages.update(page_id=page_id, properties=data)
            logger.info(f"Updated record with service_id: {service_id}")
        else:
            self.notion.pages.create(parent={"database_id": self.database_id}, properties=data)
            logger.info(f"Created new record with service_id: {service_id}")

    def _delete_record_from_notion(self, service_id):
        """Архівує запис з бази Notion замість видалення."""
        query_response = self.notion.databases.query(
            database_id=self.database_id,
            filter={"property": "ID Service", "rich_text": {"equals": str(service_id)}}
        )
        
        pages = query_response.get("results", [])
        
        if pages:
            for page in pages:
                page_id = page['id']
                try:
                    # Архівуємо сторінку замість видалення
                    self.notion.pages.update(page_id=page_id, archived=True)
                    logger.info(f"Archived record with service_id: {service_id} and page_id: {page_id}")
                except Exception as e:
                    logger.error(f"Failed to archive page with service_id: {service_id}. Error: {str(e)}")
        else:
            logger.warning(f"No page found for service_id: {service_id}")

    

# синхронізуємо ордери
class NotionConnector:
    def __init__(self, notion_token, database_id):
        self.notion = Client(auth=notion_token)
        self.database_id = database_id

    def calculate_record_hash(self, record):
        """
        Calculate a hash for the record properties to check for changes.
        """
        properties_str = str(record.get("properties", {}))
        return md5(properties_str.encode("utf-8")).hexdigest()

    def sync_orders(self):
        retries = 3
        timeout = 5
        records_synced = 0
        total_records = 0

        for attempt in range(1, retries + 1):
            try:
                response = self.notion.databases.query(database_id=self.database_id)
                notion_records = response.get("results", [])
                notion_ids = set(record["id"] for record in notion_records)
                total_records = len(notion_records)
                logger.info(f"Fetched {total_records} records from Notion.")
                print(f"📊 Fetched {total_records} records.")

                # Fetch all local records
                local_records = NotionOrders.objects.all()
                local_ids = set(record.order_id for record in local_records)

                # Detect deleted records
                deleted_ids = local_ids - notion_ids
                if deleted_ids:
                    NotionOrders.objects.filter(order_id__in=deleted_ids).delete()
                    logger.info(f"Deleted {len(deleted_ids)} records removed from Notion.")

                for record in notion_records:
                    try:
                        properties = record.get("properties", {})
                        order_id = record.get("id", "Unknown Order ID")

                        # Extract fields
                        name = properties.get("Name service", {}).get("title", [{}])[0].get("text", {}).get("content", "Unnamed Service")
                        service_name = (
                            properties.get("Services and category text", {})
                            .get("rollup", {})
                            .get("array", [{}])[0]
                            .get("title", [{}])[0]
                            .get("plain_text", "Unknown Service")
                        )
                        service_id = int(
                            properties.get("ID Service", {})
                            .get("rich_text", [{}])[0]
                            .get("text", {})
                            .get("content", 0)
                        )
                        order_cost = float(
                            properties.get("Order Cost", {})
                            .get("formula", {})
                            .get("number", 0.0)
                        )
                        finish_date = (
                            properties.get("Finish Date", {})
                            .get("date", {})
                            .get("start", None)
                        )
                        responsible = (
                            properties.get("Responsible", {})
                            .get("people", [{}])[0]
                            .get("name", "Unknown Responsible")
                        )
                        business_unit = (
                            properties.get("Business Unit", {})
                            .get("rollup", {})
                            .get("array", [{}])[0]
                            .get("rich_text", [{}])[0]
                            .get("text", {})
                            .get("content", "Unknown Business Unit")
                        )
                        business_unit_id = int(
                            properties.get("BU ID", {})
                            .get("rollup", {})
                            .get("array", [{}])[0]
                            .get("number", 0)
                        )

                        # Calculate hash for current record
                        current_hash = self.calculate_record_hash(record)

                        # Check if record exists and has changed
                        existing_record = NotionOrders.objects.filter(order_id=order_id).first()
                        if existing_record:
                            # Check for changes in any critical fields, even if hash is the same
                            if existing_record.record_hash != current_hash or existing_record.order_cost != order_cost or existing_record.finish_date != finish_date:
                                existing_record.order_cost = order_cost
                                existing_record.finish_date = finish_date
                                existing_record.record_hash = current_hash
                                existing_record.save()
                                logger.info(f"✅ Updated record: {order_id}")
                            else:
                                logger.info(f"✅ No changes for record: {order_id}")
                                continue  # Skip if no changes
                        else:
                            # New record
                            NotionOrders.objects.create(
                                order_id=order_id,
                                name=name,
                                service_name=service_name,
                                service_id=service_id,
                                order_cost=order_cost,
                                finish_date=finish_date,
                                responsible=responsible,
                                business_unit=business_unit,
                                business_unit_id=business_unit_id,
                                record_hash=current_hash,
                            )
                            logger.info(f"✅ Created new record: {order_id}")

                        records_synced += 1
                    except Exception as record_error:
                        logger.warning(f"❌ Failed to sync record: {record.get('id')}")
                        logger.warning(record_error)

                break  # Exit loop on success

            except Exception as e:
                logger.error(f"Attempt {attempt} failed. Retrying in {timeout} seconds...")
                time.sleep(timeout)
                timeout *= 2

        logger.info(f"Sync completed. {records_synced}/{total_records} records synced.")
        return f"Sync completed. {records_synced}/{total_records} records synced."
