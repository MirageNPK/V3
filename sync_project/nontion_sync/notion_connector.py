import time
import logging
from notion_client import Client
from .models import NotionOrders
from django.db.models import Sum, F,Q
from datetime import datetime
from django.db.models.functions import ExtractMonth
from hashlib import md5
from decimal import Decimal
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
                    .values('business_unit_id', 'business_unit')
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
                notion_service_ids = set()

                for page in notion_pages:
                    rich_text = page['properties']['BU ID']['rich_text']
                    if not rich_text:
                        # Архівуємо сторінки без BU ID
                        page_id = page['id']
                        self._archive_page(page_id)
                        logger.info(f"Archived page with missing BU ID: {page_id}")
                    else:
                        notion_service_ids.add(rich_text[0]['text']['content'])

                # Створення нових або оновлення записів
                for res in business_unit_data:
                    notion_data = self._prepare_service_data(res)
                    self._update_or_create_record(res['business_unit_id'], notion_data)
                    records_synced += 1
                    notion_service_ids.discard(str(res['business_unit_id']))

                # Видаляємо з Notion сервіси, яких немає в нових даних
                for service_id_to_remove in notion_service_ids:
                    self._delete_record_from_notion(service_id_to_remove)

                logger.info(f"✅ Successfully synced {records_synced} records.")
                break

            except Exception as e:
                logger.error(f"Attempt {attempt} failed: {str(e)}. Retrying in {timeout} seconds...")
                time.sleep(timeout)
                timeout *= 2

        return f"Sync completed. {records_synced} records synced."

    def _prepare_service_data(self, service):
        """Підготовка даних для передачі в Notion."""
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
            "BU ID": {
                "rich_text": [{"type": "text", "text": {"content": str(service['business_unit_id'])}}]
            },
            **{key: {"number": float(value)} for key, value in month_columns.items()},
        }

    def _update_or_create_record(self, business_unit_id, data):
        """Оновлює або створює запис у базі Notion."""
        query_response = self.notion.databases.query(
            database_id=self.database_id,
            filter={"property": "BU ID", "rich_text": {"equals": str(business_unit_id)}}
        )
        pages = query_response.get("results", [])

        if pages:
            page_id = pages[0]['id']
            self.notion.pages.update(page_id=page_id, properties=data)
            logger.info(f"Updated record for BU ID: {business_unit_id}")
        else:
            self.notion.pages.create(parent={"database_id": self.database_id}, properties=data)
            logger.info(f"Created new record for BU ID: {business_unit_id}")

    def _delete_record_from_notion(self, business_unit_id):
        """Архівує запис з бази Notion."""
        query_response = self.notion.databases.query(
            database_id=self.database_id,
            filter={"property": "BU ID", "rich_text": {"equals": str(business_unit_id)}}
        )
        pages = query_response.get("results", [])

        if pages:
            for page in pages:
                page_id = page['id']
                self._archive_page(page_id)

    def _archive_page(self, page_id):
        """Архівує сторінку у базі Notion."""
        try:
            self.notion.pages.update(page_id=page_id, archived=True)
            logger.info(f"Successfully archived page with ID: {page_id}")
        except Exception as e:
            logger.error(f"Failed to archive page with ID: {page_id}. Error: {str(e)}")




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
                # Отримуємо всі записи з бази Notion
                response = self.notion.databases.query(database_id=self.database_id)
                notion_records = response.get("results", [])
                total_records = len(notion_records)
                notion_ids = set(record["id"] for record in notion_records)

                logger.info(f"Fetched {total_records} records from Notion.")
                print(f"📊 Fetched {total_records} records.")

                # Отримуємо всі локальні записи
                local_records = NotionOrders.objects.all()
                local_ids = set(record.order_id for record in local_records)

                # Видаляємо записи, яких більше немає в Notion
                deleted_ids = local_ids - notion_ids
                if deleted_ids:
                    NotionOrders.objects.filter(order_id__in=deleted_ids).delete()
                    logger.info(f"Deleted {len(deleted_ids)} records removed from Notion.")

                # Оновлення та створення записів
                for record in notion_records:
                    try:
                        properties = record.get("properties", {})
                        order_id = record.get("id", "Unknown Order ID")

                        # Витягуємо дані з властивостей Notion
                        name = properties.get("Name service", {}).get("title", [{}])[0].get("text", {}).get("content", "Unnamed Service")
                        service_name = (
                            properties.get("Services and category text", {})
                            .get("rollup", {})
                            .get("array", [{}])[0]
                            .get("rich_text", [{}])[0]
                            .get("text", {})
                            .get("content", "Unknown Service")
                        )
                        service_id = (
                            properties.get("ID serv", {})
                            .get("rollup", {})
                            .get("array", [{}])[0]
                            .get("rich_text", [{}])[0]
                            .get("text", {})
                            .get("content", "0")
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

                        # Рахуємо хеш запису для перевірки змін
                        current_hash = self.calculate_record_hash(record)

                        # Перевіряємо, чи існує запис у локальній базі
                        existing_record = NotionOrders.objects.filter(order_id=order_id).first()

                        if existing_record:
                            # Оновлюємо, якщо є зміни
                            if (
                                existing_record.record_hash != current_hash or
                                existing_record.order_cost != order_cost or
                                existing_record.finish_date != finish_date or
                                existing_record.service_id != service_id or
                                existing_record.business_unit_id != business_unit_id
                            ):
                                existing_record.name = name
                                existing_record.service_name = service_name
                                existing_record.service_id = service_id
                                existing_record.order_cost = order_cost
                                existing_record.finish_date = finish_date
                                existing_record.responsible = responsible
                                existing_record.business_unit = business_unit
                                existing_record.business_unit_id = business_unit_id
                                existing_record.record_hash = current_hash
                                existing_record.save()
                                logger.info(f"✅ Updated record: {order_id}")
                            else:
                                logger.info(f"✅ No changes for record: {order_id}")
                                continue  # Пропускаємо, якщо змін немає
                        else:
                            # Створюємо новий запис
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

                break  # Успішна синхронізація, вихід із циклу
            except Exception as e:
                logger.error(f"Attempt {attempt} failed. Retrying in {timeout} seconds...")
                time.sleep(timeout)
                timeout *= 2

        logger.info(f"Sync completed. {records_synced}/{total_records} records synced.")
        return f"Sync completed. {records_synced}/{total_records} records synced."



class WorkloadCalculator:
    def __init__(self, notion_token, project_tasks_database_id, closing_tasks_database_id, orders_database_id):
        self.notion = Client(auth=notion_token)
        self.project_tasks_database_id = project_tasks_database_id
        self.closing_tasks_database_id = closing_tasks_database_id
        self.orders_database_id = orders_database_id

    def get_all_tasks(self, database_id):
        tasks = []
        has_more = True
        start_cursor = None

        while has_more:
            try:
                response = self.notion.databases.query(
                    database_id=database_id,
                    start_cursor=start_cursor
                )
                tasks.extend(response.get("results", []))
                has_more = response.get("has_more", False)
                start_cursor = response.get("next_cursor")
            except Exception as e:
                logger.error(f"Error fetching tasks from database {database_id}: {e}")
                break
        return tasks

    def calculate_workload(self):
        workload_data = {}
        workload_hours_data = {}

        def add_hours(person, month_key, hours):
            if person not in workload_data:
                workload_data[person] = {}
            if month_key not in workload_data[person]:
                workload_data[person][month_key] = Decimal("0")
            workload_data[person][month_key] += Decimal(hours) / Decimal("130")

        # Обробка завдань проекту
        project_tasks = self.get_all_tasks(self.project_tasks_database_id)
        logger.info(f"Number of project tasks: {len(project_tasks)}")
        for task in project_tasks:
            properties = task.get("properties", {})
            if not properties:
                logger.info(f"Skipping task due to missing properties: {task}")
                continue

            people = properties.get("Person", {}).get("people", [])
            person = people[0].get("name", "Unknown") if people else "Нерозподілені години"
            hours = properties.get("Hours plan", {}).get("number")
            if hours is None or hours <= 0:
                continue

            finish_date = properties.get("Finish", {}).get("date", {}).get("start")
            if not finish_date:
                continue

            try:
                month_key = datetime.strptime(finish_date, "%Y-%m-%d").strftime("%m.%y")
                add_hours(person, month_key, hours)
            except ValueError as e:
                logger.error(f"Error processing date for {person}: {e}")

        # Fetch closing tasks
        closing_tasks = self.get_all_tasks(self.closing_tasks_database_id)
        logger.info(f"Number of closing tasks: {len(closing_tasks)}")
        for task in closing_tasks:
            properties = task.get("properties", {})
            if not properties:
                continue

            people = properties.get("Person", {}).get("people", [])
            person = people[0].get("name", "Unknown") if people else "Нерозподілені години"
            hours = properties.get("Plan Hours", {}).get("number")
            ddl_date = properties.get("Data DDL", {}).get("formula", {}).get("date", {}).get("start", None)

            if hours is None or not ddl_date:
                continue

            try:
                parsed_date = datetime.fromisoformat(ddl_date.replace("Z", "+00:00"))
                month_key = parsed_date.strftime("%m.%y")
                add_hours(person, month_key, hours)
            except ValueError as e:
                logger.error(f"Error processing DDL date for {person}: {e}")

        # Fetch orders
        orders = self.get_all_tasks(self.orders_database_id)
        logger.info(f"Number of orders: {len(orders)}")
        for order in orders:
            properties = order.get("properties", {})
            if not properties:
                continue

            people = properties.get("Responsible", {}).get("people", [])
            person = people[0].get("name", "Unknown") if people else "Нерозподілені години"
            hours = properties.get("Plan hours", {}).get("number")
            ddl_date = properties.get("DDL", {}).get("date", {}).get("start")

            if hours is None or not ddl_date:
                continue

            try:
                month_key = datetime.strptime(ddl_date, "%Y-%m-%d").strftime("%m.%y")
                add_hours(person, month_key, hours)
            except ValueError as e:
                logger.error(f"Error processing DDL date for {person}: {e}")

        # Calculate final workload hours
        for person, months in workload_data.items():
            workload_hours_data[person] = {}
            for month, coef in months.items():
                workload_data[person][month] = float(round(coef, 2))
                hours = float(round(coef * Decimal("130"), 2))
                workload_hours_data[person][f"{month}h"] = hours

        return workload_data, workload_hours_data

class NotionWorkloadSync:
    def __init__(self, notion_token, database_id):
        self.notion = Client(auth=notion_token)
        self.database_id = database_id

    def sync_workload(self, workload_data, workload_hours_data):
        query_response = self.notion.databases.query(database_id=self.database_id)
        notion_pages = query_response.get("results", [])

        if notion_pages:
            first_page_properties = notion_pages[0].get("properties", {})
            logger.info(f"Database Properties: {list(first_page_properties.keys())}")

        month_keys = [
            "01.25", "02.25", "03.25", "04.25", "05.25", "06.25", 
            "07.25", "08.25", "09.25", "10.25", "11.25", "12.25",
            "01.26", "02.26", "03.26", "04.26", "05.26", "06.26"
        ]
        month_keys_hours = [f"{month}h" for month in month_keys]

        retries = 3
        timeout = 5
        records_synced = 0

        for attempt in range(1, retries + 1):
            try:
                query_response = self.notion.databases.query(database_id=self.database_id)
                notion_pages = query_response.get("results", [])

                notion_person_pages = {}
                for page in notion_pages:
                    properties = page.get("properties", {})
                    responsible_name = properties.get("Responsible Name", {}).get("title", [])
                    if responsible_name:
                        name = responsible_name[0]["text"]["content"]
                        notion_person_pages[name] = page["id"]

                processed_people = set()

                for person, months in workload_data.items():
                    notion_data = self._prepare_workload_data(
                        person, months, month_keys, workload_hours_data.get(person, {}), month_keys_hours
                    )
                    logger.info(f"Prepared data for {person}: {notion_data}")

                    existing_page_id = notion_person_pages.get(person)
                    if existing_page_id:
                        existing_page = self.notion.pages.retrieve(page_id=existing_page_id)
                        existing_properties = existing_page.get("properties", {})

                        updated_data = {
                            key: notion_data[key]
                            for key in notion_data
                            if key in (month_keys + month_keys_hours) and notion_data[key] != existing_properties.get(key)
                        }

                        if updated_data:
                            self._update_record(existing_page_id, updated_data)
                        else:
                            logger.info(f"No changes for {person}, skipping update.")
                    else:
                        self._create_record(notion_data)

                    records_synced += 1
                    processed_people.add(person)

                records_deleted = 0
                for person_to_remove in set(notion_person_pages.keys()) - processed_people:
                    try:
                        self._delete_record_from_notion(notion_person_pages[person_to_remove])
                        records_deleted += 1
                    except Exception as e:
                        logger.error(f"Failed to delete record for {person_to_remove}: {str(e)}")

                logger.info(f"\u2705 Successfully synced {records_synced} records and deleted {records_deleted} records.")
                break

            except Exception as e:
                logger.error(f"Attempt {attempt} failed: {str(e)}. Retrying in {timeout} seconds...")
                time.sleep(timeout)
                timeout *= 2

        return f"Sync completed. {records_synced} records synced."

    def _prepare_workload_data(self, person, months, month_keys, hours_data, month_keys_hours):
        month_columns = {}

        for month in month_keys:
            month_columns[month] = {"number": months.get(month, 0) or 0}

        for month in month_keys_hours:
            month_columns[month] = {"number": hours_data.get(month, 0) or 0}

        month_columns["Responsible Name"] = {
            "title": [{"type": "text", "text": {"content": person}}]
        }

        return month_columns

    def _update_record(self, page_id, data):
        try:
            if data:
                logger.info(f"Updating record for page {page_id} with data: {data}")
                response = self.notion.pages.update(page_id=page_id, properties=data)
                if response.get("properties"):
                    logger.info(f"Successfully updated record for page {page_id}: {response}")
                else:
                    logger.warning(f"Update for page {page_id} failed. Response: {response}")
            else:
                logger.info(f"No fields to update for page {page_id}. Skipping update.")

        except Exception as e:
            logger.error(f"Failed to update record for page {page_id}: {e}")

    def _create_record(self, data):
        try:
            logger.info(f"Creating record with data: {data}")
            response = self.notion.pages.create(parent={"database_id": self.database_id}, properties=data)
            logger.info(f"Successfully created record: {response}")
        except Exception as e:
            logger.error(f"Failed to create record: {e}")

    def _delete_record_from_notion(self, page_id):
        try:
            logger.info(f"Archiving record with page ID {page_id}")
            response = self.notion.pages.update(page_id=page_id, archived=True)
            logger.info(f"Successfully archived record: {response}")
        except Exception as e:
            logger.error(f"Failed to archive record with page ID {page_id}: {e}")
            raise



# class WorkloadCalculator:
#     def __init__(self, notion_token, project_tasks_database_id, closing_tasks_database_id, orders_database_id):
#         self.notion = Client(auth=notion_token)
#         self.project_tasks_database_id = project_tasks_database_id
#         self.closing_tasks_database_id = closing_tasks_database_id
#         self.orders_database_id = orders_database_id

#     def get_all_tasks(self, database_id):
#         tasks = []
#         has_more = True
#         start_cursor = None

#         while has_more:
#             try:
#                 response = self.notion.databases.query(
#                     database_id=database_id,
#                     start_cursor=start_cursor
#                 )
#                 tasks.extend(response.get("results", []))
#                 has_more = response.get("has_more", False)
#                 start_cursor = response.get("next_cursor")
#             except Exception as e:
#                 logger.error(f"Error fetching tasks from database {database_id}: {e}")
#                 break
#         return tasks

#     def calculate_workload(self):
#         workload_data = {}

#         # Fetch project tasks
#         project_tasks = self.get_all_tasks(self.project_tasks_database_id)
#         logger.info(f"Number of project tasks: {len(project_tasks)}")
#         for task in project_tasks:
#             properties = task.get("properties", {})
#             if not properties:
#                 logger.info(f"Skipping task due to missing properties: {task}")
#                 continue

#             people = properties.get("Person", {}).get("people", [])
#             person = people[0].get("name", "Unknown") if people else "Нерозподілені години"
#             hours = properties.get("Hours plan", {}).get("number")
#             if hours is None or hours <= 0:
#                 continue

#             finish_date = properties.get("Finish", {}).get("date", {}).get("start")
#             if not finish_date:
#                 continue

#             try:
#                 month_key = datetime.strptime(finish_date, "%Y-%m-%d").strftime("%m.%y")
#                 workload_data.setdefault(person, {}).setdefault(month_key, 0)
#                 workload_data[person][month_key] += hours
#             except ValueError as e:
#                 logger.error(f"Error processing date for {person}: {e}")

#         # Fetch closing tasks
#         closing_tasks = self.get_all_tasks(self.closing_tasks_database_id)
#         logger.info(f"Number of closing tasks: {len(closing_tasks)}")
#         for task in closing_tasks:
#             properties = task.get("properties", {})
#             if not properties:
#                 continue

#             people = properties.get("Person", {}).get("people", [])
#             person = people[0].get("name", "Unknown") if people else "Нерозподілені години"
#             hours = properties.get("Plan Hours", {}).get("number")
#             ddl_date = properties.get("Data DDL", {}).get("formula", {}).get("string")

#             if hours is None or hours <= 0 or not ddl_date:
#                 continue

#             try:
#                 month_key = datetime.strptime(ddl_date, "%Y-%m-%d").strftime("%m.%y")
#                 workload_data.setdefault(person, {}).setdefault(month_key, 0)
#                 workload_data[person][month_key] += hours
#             except ValueError as e:
#                 logger.error(f"Error processing DDL date for {person}: {e}")

#         # Fetch orders
#         orders = self.get_all_tasks(self.orders_database_id)
#         logger.info(f"Number of orders: {len(orders)}")
#         for order in orders:
#             properties = order.get("properties", {})
#             if not properties:
#                 continue

#             people = properties.get("Responsible", {}).get("people", [])
#             person = people[0].get("name", "Unknown") if people else "Нерозподілені години"
#             hours = properties.get("Plan hours", {}).get("number")
#             ddl_date = properties.get("DDL", {}).get("date", {}).get("start")

#             if hours is None or hours <= 0 or not ddl_date:
#                 continue

#             try:
#                 month_key = datetime.strptime(ddl_date, "%Y-%m-%d").strftime("%m.%y")
#                 workload_data.setdefault(person, {}).setdefault(month_key, 0)
#                 workload_data[person][month_key] += hours
#             except ValueError as e:
#                 logger.error(f"Error processing DDL date for {person}: {e}")

#         # Convert hours into workload ratios
#         for person, months in workload_data.items():
#             for month, hours in months.items():
#                 workload_data[person][month] = round(hours / 130, 2)

#         return workload_data

# class NotionWorkloadSync:
#     def __init__(self, notion_token, database_id):
#         self.notion = Client(auth=notion_token)
#         self.database_id = database_id

#     def sync_workload(self, workload_data):
#         month_keys = [
#             "01.25", "02.25", "03.25", "04.25", "05.25", "06.25", 
#             "07.25", "08.25", "09.25", "10.25", "11.25", "12.25",
#             "01.26", "02.26", "03.26", "04.26", "05.26", "06.26"
#         ]

#         retries = 3
#         timeout = 5
#         records_synced = 0

#         for attempt in range(1, retries + 1):
#             try:
#                 query_response = self.notion.databases.query(database_id=self.database_id)
#                 notion_pages = query_response.get("results", [])

#                 notion_person_pages = {}
#                 for page in notion_pages:
#                     properties = page.get("properties", {})
#                     responsible_name = properties.get("Responsible Name", {}).get("title", [])
#                     if responsible_name:
#                         name = responsible_name[0]["text"]["content"]
#                         notion_person_pages[name] = page["id"]

#                 processed_people = set()

#                 for person, months in workload_data.items():
#                     notion_data = self._prepare_workload_data(person, months, month_keys)
#                     logger.info(f"Prepared data for {person}: {notion_data}")

#                     existing_page_id = notion_person_pages.get(person)
#                     if existing_page_id:
#                         existing_page = self.notion.pages.retrieve(page_id=existing_page_id)
#                         existing_properties = existing_page.get("properties", {})

#                         updated_data = False
#                         for month_key in month_keys:
#                             # Перевіряємо, чи є зміни для місяців
#                             current_value = existing_properties.get(month_key, {}).get("number", 0)
#                             new_value = notion_data.get(month_key, {}).get("number", 0)

#                             # Якщо нове значення відрізняється від поточного, оновлюємо
#                             if current_value != new_value:
#                                 existing_properties[month_key] = {"number": new_value}
#                                 updated_data = True

#                         # Оновлюємо запис, якщо є зміни
#                         if updated_data:
#                             self._update_record(existing_page_id, existing_properties)
#                         else:
#                             logger.info(f"No changes for {person}, skipping update.")
#                     else:
#                         self._create_record(notion_data)

#                     records_synced += 1
#                     processed_people.add(person)

#                 # Видаляємо записи, яких немає в новому списку
#                 records_deleted = 0
#                 for person_to_remove in set(notion_person_pages.keys()) - processed_people:
#                     try:
#                         self._delete_record_from_notion(notion_person_pages[person_to_remove])
#                         records_deleted += 1
#                     except Exception as e:
#                         logger.error(f"Failed to delete record for {person_to_remove}: {str(e)}")

#                 logger.info(f"\u2705 Successfully synced {records_synced} records and deleted {records_deleted} records.")
#                 break

#             except Exception as e:
#                 logger.error(f"Attempt {attempt} failed: {str(e)}. Retrying in {timeout} seconds...")
#                 time.sleep(timeout)
#                 timeout *= 2

#         return f"Sync completed. {records_synced} records synced."

#     def _prepare_workload_data(self, person, months, month_keys):
#         # Підготовка даних для запису, використовуючи місяці та значення
#         month_columns = {}
#         for month in month_keys:
#             month_columns[month] = {"number": months.get(month, 0) or 0}
        
#         return {
#             "Responsible Name": {
#                 "title": [{"type": "text", "text": {"content": person}}]
#             },
#             **month_columns,
#         }

#     def _update_record(self, page_id, data):
#         try:
#             logger.info(f"Updating record for page {page_id} with data: {data}")
#             response = self.notion.pages.update(page_id=page_id, properties=data)
#             if response.get("properties"):
#                 logger.info(f"Successfully updated record for page {page_id}: {response}")
#             else:
#                 logger.warning(f"Update for page {page_id} failed. Response: {response}")
#         except Exception as e:
#             logger.error(f"Failed to update record for page {page_id}: {e}")

#     def _create_record(self, data):
#         try:
#             logger.info(f"Creating record with data: {data}")
#             response = self.notion.pages.create(parent={"database_id": self.database_id}, properties=data)
#             logger.info(f"Successfully created record: {response}")
#         except Exception as e:
#             logger.error(f"Failed to create record: {e}")

#     def _delete_record_from_notion(self, page_id):
#         try:
#             logger.info(f"Archiving record with page ID {page_id}")
#             response = self.notion.pages.update(page_id=page_id, archived=True)
#             logger.info(f"Successfully archived record: {response}")
#         except Exception as e:
#             logger.error(f"Failed to archive record with page ID {page_id}: {e}")
#             raise


class WorkloadTempCalculator:
    def __init__(self, notion_token, project_tasks_database_id, closing_tasks_database_id, orders_database_id):
        self.notion = Client(auth=notion_token)
        self.project_tasks_database_id = project_tasks_database_id
        self.closing_tasks_database_id = closing_tasks_database_id
        self.orders_database_id = orders_database_id

    def get_all_tasks(self, database_id):
        tasks = []
        has_more = True
        start_cursor = None

        while has_more:
            try:
                response = self.notion.databases.query(
                    database_id=database_id,
                    start_cursor=start_cursor
                )
                tasks.extend(response.get("results", []))
                has_more = response.get("has_more", False)
                start_cursor = response.get("next_cursor")
            except Exception as e:
                logger.error(f"Error fetching tasks from database {database_id}: {e}")
                break
        return tasks

    def calculate_workload(self):
        workload_data = {}

        # Fetch project tasks
        project_tasks = self.get_all_tasks(self.project_tasks_database_id)
        logger.info(f"Number of project tasks: {len(project_tasks)}")
        for task in project_tasks:
          
            properties = task.get("properties", {})
            if not properties:
                logger.info(f"Skipping task due to missing properties: {task}")
                continue

            people = properties.get("Resposible", {}).get("select", {})
            person = people.get("name", "Unknown") if people else "Нерозподілені години"
            
            hours = properties.get("Hours plan", {}).get("number")
            if hours is None or hours <= 0:
                continue

            finish_date = properties.get("Finish", {}).get("date", {}).get("start")
            if not finish_date:
                continue

            try:
                month_key = datetime.strptime(finish_date, "%Y-%m-%d").strftime("%m.%y")
                workload_data.setdefault(person, {}).setdefault(month_key, 0)
                workload_data[person][month_key] += hours
            except ValueError as e:
                logger.error(f"Error processing date for {person}: {e}")

        # Fetch closing tasks
        closing_tasks = self.get_all_tasks(self.closing_tasks_database_id)
        logger.info(f"Number of closing tasks: {len(closing_tasks)}")
        for task in closing_tasks:
            
            properties = task.get("properties", {})
            if not properties:
                continue

            people = properties.get("Who", {}).get("select", {})
            person = people.get("name", "Unknown") if people else "Нерозподілені години"
            
            hours = properties.get("Plan Hours", {}).get("number")
            ddl_date = properties.get("Data DDL", {}).get("formula", {}).get("date", {}).get("start", None)
            

            if hours is None or hours <= 0 or not ddl_date:
                continue

            try:
                parsed_date = datetime.fromisoformat(ddl_date.replace("Z", "+00:00"))  # Враховуємо часову зону
                month_key = parsed_date.strftime("%m.%y")  # Форматуємо місяць.рік
                
                workload_data.setdefault(person, {}).setdefault(month_key, 0)
                workload_data[person][month_key] += hours
            except ValueError as e:
                logger.error(f"Error processing DDL date for {person}: {e}")

        # Fetch orders
        orders = self.get_all_tasks(self.orders_database_id)
        logger.info(f"Number of orders: {len(orders)}")
        for order in orders:
            properties = order.get("properties", {})
            if not properties:
                continue

            people = properties.get("Responsible", {}).get("people", [])
            person = people[0].get("name", "Unknown") if people else "Нерозподілені години"
            hours = properties.get("Plan hours", {}).get("number")
            ddl_date = properties.get("DDL", {}).get("date", {}).get("start")

            if hours is None or hours <= 0 or not ddl_date:
                continue

            try:
                month_key = datetime.strptime(ddl_date, "%Y-%m-%d").strftime("%m.%y")
                workload_data.setdefault(person, {}).setdefault(month_key, 0)
                workload_data[person][month_key] += hours
            except ValueError as e:
                logger.error(f"Error processing DDL date for {person}: {e}")

        # Convert hours into workload ratios
        for person, months in workload_data.items():
            for month, hours in months.items():
                workload_data[person][month] = round(hours / 130, 2)

        return workload_data

class NotionWorkloadtempSync:
    def __init__(self, notion_token, database_id):
        self.notion = Client(auth=notion_token)
        self.database_id = database_id

    def sync_workload(self, workload_data):
        month_keys = [
            "01.25", "02.25", "03.25", "04.25", "05.25", "06.25", 
            "07.25", "08.25", "09.25", "10.25", "11.25", "12.25",
            "01.26", "02.26", "03.26", "04.26", "05.26", "06.26"
        ]

        retries = 3
        timeout = 5
        records_synced = 0

        for attempt in range(1, retries + 1):
            try:
                query_response = self.notion.databases.query(database_id=self.database_id)
                notion_pages = query_response.get("results", [])

                notion_person_pages = {}
                for page in notion_pages:
                    properties = page.get("properties", {})
                    responsible_name = properties.get("Responsible Name", {}).get("title", [])
                    if responsible_name:
                        name = responsible_name[0]["text"]["content"]
                        notion_person_pages[name] = page["id"]

                processed_people = set()

                for person, months in workload_data.items():
                    notion_data = self._prepare_workload_data(person, months, month_keys)
                    logger.info(f"Prepared data for {person}: {notion_data}")

                    existing_page_id = notion_person_pages.get(person)
                    if existing_page_id:
                        existing_page = self.notion.pages.retrieve(page_id=existing_page_id)
                        existing_properties = existing_page.get("properties", {})

                        updated_data = False
                        for month_key in month_keys:
                            # Перевіряємо, чи є зміни для місяців
                            current_value = existing_properties.get(month_key, {}).get("number", 0)
                            new_value = notion_data.get(month_key, {}).get("number", 0)

                            # Якщо нове значення відрізняється від поточного, оновлюємо
                            if current_value != new_value:
                                existing_properties[month_key] = {"number": new_value}
                                updated_data = True

                        # Оновлюємо запис, якщо є зміни
                        if updated_data:
                            self._update_record(existing_page_id, existing_properties)
                        else:
                            logger.info(f"No changes for {person}, skipping update.")
                    else:
                        self._create_record(notion_data)

                    records_synced += 1
                    processed_people.add(person)

                # Видаляємо записи, яких немає в новому списку
                records_deleted = 0
                for person_to_remove in set(notion_person_pages.keys()) - processed_people:
                    try:
                        self._delete_record_from_notion(notion_person_pages[person_to_remove])
                        records_deleted += 1
                    except Exception as e:
                        logger.error(f"Failed to delete record for {person_to_remove}: {str(e)}")

                logger.info(f"\u2705 Successfully synced {records_synced} records and deleted {records_deleted} records.")
                break

            except Exception as e:
                logger.error(f"Attempt {attempt} failed: {str(e)}. Retrying in {timeout} seconds...")
                time.sleep(timeout)
                timeout *= 2

        return f"Sync completed. {records_synced} records synced."

    def _prepare_workload_data(self, person, months, month_keys):
        # Підготовка даних для запису, використовуючи місяці та значення
        month_columns = {}
        for month in month_keys:
            month_columns[month] = {"number": months.get(month, 0) or 0}
        
        return {
            "Responsible Name": {
                "title": [{"type": "text", "text": {"content": person}}]
            },
            **month_columns,
        }

    def _update_record(self, page_id, data):
        try:
            logger.info(f"Updating record for page {page_id} with data: {data}")
            response = self.notion.pages.update(page_id=page_id, properties=data)
            if response.get("properties"):
                logger.info(f"Successfully updated record for page {page_id}: {response}")
            else:
                logger.warning(f"Update for page {page_id} failed. Response: {response}")
        except Exception as e:
            logger.error(f"Failed to update record for page {page_id}: {e}")

    def _create_record(self, data):
        try:
            logger.info(f"Creating record with data: {data}")
            response = self.notion.pages.create(parent={"database_id": self.database_id}, properties=data)
            logger.info(f"Successfully created record: {response}")
        except Exception as e:
            logger.error(f"Failed to create record: {e}")

    def _delete_record_from_notion(self, page_id):
        try:
            logger.info(f"Archiving record with page ID {page_id}")
            response = self.notion.pages.update(page_id=page_id, archived=True)
            logger.info(f"Successfully archived record: {response}")
        except Exception as e:
            logger.error(f"Failed to archive record with page ID {page_id}: {e}")
            raise



