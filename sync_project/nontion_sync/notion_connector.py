import time
import logging
from notion_client import Client
from .models import NotionOrders
from django.db.models import Sum
from datetime import datetime
from django.db.models.functions import ExtractMonth

logger = logging.getLogger(__name__)

from datetime import datetime

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
                # Group data by service_id and calculate monthly earnings
                services = (
                    NotionOrders.objects
                    .values('service_id', 'service_name', 'finish_date')
                    .annotate(
                        jan=Sum('order_cost', filter=ExtractMonth('finish_date') == 1),
                        feb=Sum('order_cost', filter=ExtractMonth('finish_date') == 2),
                        mar=Sum('order_cost', filter=ExtractMonth('finish_date') == 3),
                        apr=Sum('order_cost', filter=ExtractMonth('finish_date') == 4),
                        may=Sum('order_cost', filter=ExtractMonth('finish_date') == 5),
                        jun=Sum('order_cost', filter=ExtractMonth('finish_date') == 6),
                        jul=Sum('order_cost', filter=ExtractMonth('finish_date') == 7),
                        aug=Sum('order_cost', filter=ExtractMonth('finish_date') == 8),
                        sep=Sum('order_cost', filter=ExtractMonth('finish_date') == 9),
                        oct=Sum('order_cost', filter=ExtractMonth('finish_date') == 10),
                        nov=Sum('order_cost', filter=ExtractMonth('finish_date') == 11),
                        dec=Sum('order_cost', filter=ExtractMonth('finish_date') == 12),
                    )
                )

                # Sync data to Notion
                for service in services:
                    notion_data = self._prepare_service_data(service)
                    self._update_or_create_record(service['service_id'], notion_data)
                    records_synced += 1

                logger.info(f"✅ Successfully synced {records_synced} records.")
                break  # Exit loop if successful

            except Exception as e:
                logger.error(f"Attempt {attempt} failed: {str(e)}. Retrying in {timeout} seconds...")
                time.sleep(timeout)
                timeout *= 2

        return f"Sync completed. {records_synced} records synced."

    def _prepare_service_data(self, service):
        """Prepares data payload for Notion."""
        # Отримуємо місяць з дати finish_date
        finish_date = service.get('finish_date')
        if isinstance(finish_date, str):
            finish_date = datetime.strptime(finish_date, '%Y-%m-%d')

        # Заповнюємо значення для місяців
        month_columns = {
            "1.25": 0,  # Січень
            "2.25": 0,  # Лютий
            "3.25": 0,  # Березень
            "4.25": 0,  # Квітень
            "5.25": 0,  # Травень
            "6.25": 0,  # Червень
            "7.25": 0,  # Липень
            "8.25": 0,  # Серпень
            "9.25": 0,  # Вересень
            "10.25": 0, # Жовтень
            "11.25": 0, # Листопад
            "12.25": 0  # Грудень
        }

        # Якщо дата є, визначаємо місяць і записуємо значення в відповідну колонку
        if finish_date:
            month = finish_date.month
            column_name = f"{month}.25"
            if column_name in month_columns:
                month_columns[column_name] = float(service.get(f'{finish_date.strftime("%b").lower()}', 0))  # отримуємо значення для цього місяця

        return {
            "Service Name": {
                "title": [{"type": "text", "text": {"content": service['service_name']}}]
            },
            **{key: {"number": value} for key, value in month_columns.items()},
            "ID Service": {"rich_text": [{"type": "text", "text": {"content": str(service['service_id'])}}]}
        }

    def _update_or_create_record(self, service_id, data):
        """Updates or creates a record in the Notion database."""
        # Fetch existing pages in Notion
        query_response = self.notion.databases.query(
            database_id=self.database_id,
            filter={"property": "ID Service", "rich_text": {"equals": str(service_id)}}
        )
        pages = query_response.get("results", [])

        if pages:
            # Update the existing record
            page_id = pages[0]['id']
            self.notion.pages.update(page_id=page_id, properties=data)
            logger.info(f"Updated record with ID Service: {service_id}")
        else:
            # Create a new record
            self.notion.pages.create(parent={"database_id": self.database_id}, properties=data)
            logger.info(f"Created new record with ID Service: {service_id}")



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
