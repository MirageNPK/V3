import time
import logging
from notion_client import Client
from .models import NotionOrders
from django.db.models import Sum, F,Q
from datetime import datetime
from django.db.models.functions import ExtractMonth

logger = logging.getLogger(__name__)


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

                # Синхронізація даних у Notion
                for res in responsible_data:
                    notion_data = self._prepare_service_data(res)
                    self._update_or_create_record(res['responsible'], notion_data)
                    records_synced += 1

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

                # Синхронізація даних у Notion
                for res in business_unit_data:
                    notion_data = self._prepare_service_data(res)
                    self._update_or_create_record(res['business_unit_id'], notion_data)
                    records_synced += 1

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
                # Групуємо дані за business_unit_id і підраховуємо значення для кожного місяця
                service_data = (
                    NotionOrders.objects
                    .values('service_id', 'service_name')  # Групуємо за "business_unit_id"
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

                # Синхронізація даних у Notion
                for res in service_data:
                    notion_data = self._prepare_service_data(res)
                    self._update_or_create_record(res['service_id'], notion_data)
                    records_synced += 1

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
            "Service Name": {
                "title": [{"type": "text", "text": {"content": service['service_name']}}]
            },
            **{key: {"number": float(value)} for key, value in month_columns.items()},
        }

    def _update_or_create_record(self, service_id, data):
        """Оновлює або створює запис у базі Notion."""
        # Отримуємо наявні сторінки в Notion
        query_response = self.notion.databases.query(
            database_id=self.database_id,
            filter={"property": "ID Service", "rich_text": {"equals": str(service_id)}}
        )
        pages = query_response.get("results", [])

        if pages:
            # Оновлюємо існуючий запис
            page_id = pages[0]['id']
            self.notion.pages.update(page_id=page_id, properties=data)
            logger.info(f"Updated record with responsible: {service_id}")
        else:
            # Створюємо новий запис
            self.notion.pages.create(parent={"database_id": self.database_id}, properties=data)
            logger.info(f"Created new record with responsible: {service_id}")
    


# синхронізуємо ордери
class NotionConnector:
    def __init__(self, notion_token, database_id):
        self.notion = Client(auth=notion_token)
        self.database_id = database_id

    def sync_orders(self):
        retries = 3
        timeout = 5
        records_synced = 0
        total_records = 0

        for attempt in range(1, retries + 1):
            try:
                response = self.notion.databases.query(database_id=self.database_id)
                records = response.get("results", [])
                total_records = len(records)
                logger.info(f"Fetched {total_records} records from Notion.")
                print(f"📊 Fetched {total_records} records.")

                for record in records:
                    
                    try:
                        properties = record.get("properties", {})

                        # Unique Order ID
                        order_id = record.get("id", "Unknown Order ID")

                        # Name service
                        name = properties.get("Name service", {}).get("title", [{}])[0].get("text", {}).get("content", "Unnamed Service")

                        # Services and category text
                        service_name = (
                            properties.get("Services and category text", {})
                            .get("rollup", {})
                            .get("array", [{}])[0]
                            .get("title", [{}])[0]
                            .get("plain_text", "Unknown Service")
                        )

                        # ID Service
                        service_id = int(
                            properties.get("ID Service", {})
                            .get("rich_text", [{}])[0]
                            .get("text", {})
                            .get("content", 0)  # Default 0 if missing
                        )

                        # Order Cost
                        order_cost = float(
                            properties.get("Order Cost", {})
                            .get("formula", {})
                            .get("number", 0.0)  # Default 0.0 if missing
                        )

                        # Finish Date
                        finish_date = (
                            properties.get("Finish Date", {})
                            .get("date", {})
                            .get("start", None)  # Default None if missing
                        )

                        # Responsible
                        responsible = (
                            properties.get("Responsible", {})
                            .get("people", [{}])[0]
                            .get("name", "Unknown Responsible")
                        )

                        # Business Unit
                        business_unit = (
                            properties.get("Business Unit", {})
                            .get("rollup", {})
                            .get("array", [{}])[0]
                            .get("rich_text", [{}])[0]
                            .get("text", {})
                            .get("content", "Unknown Business Unit")
                        )
                         # Business Unit
                        business_unit_id = int(
                            properties.get("BU ID", {})
                            .get("rollup", {})
                            .get("array", [{}])[0]
                            .get("number", 0)
                        )
                        
                       
                        # Update or create the record in the database
                        NotionOrders.objects.update_or_create(
                            order_id=order_id,
                            defaults={
                                "name": name,
                                "service_name": service_name,
                                "service_id": service_id,
                                "order_cost": order_cost,
                                "finish_date": finish_date,
                                "responsible": responsible,
                                "business_unit": business_unit,
                                "business_unit_id": business_unit_id,
                            },
                        )
                        records_synced += 1
                        logger.info(f"✅ Synced record: {name}")
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
