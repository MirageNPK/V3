import requests
from notion_client import Client
import logging
import os
from datetime import datetime
import time

class NotionConnector:
    def __init__(self, notion_token, database_id, auth_endpoint, data_endpoint):
       
            
        # створення логів
        log_dir = 'logs'
        os.makedirs(log_dir, exist_ok=True)

        # Опис логування
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            filename=os.path.join(log_dir, 'notion_sync.log'),
            filemode='a'  # Append mode
        )
        
        logging.info("Initializing NotionConnector...")
        self.notion = Client(auth=notion_token)
        self.database_id = database_id.replace("-", "")
        self.auth_endpoint = auth_endpoint
        self.data_endpoint = data_endpoint

        logging.info(f"Using cleaned Database ID: {self.database_id}")
   
    # отримання тікета
    def authenticate(self, login, password):
        """Enhanced authentication with comprehensive logging"""
        logging.info("Starting authentication...")
        
        try:
            auth_payload = {"login": login, "password": password}
            logging.info(f"Auth payload: {auth_payload}")

            response = requests.post(self.auth_endpoint, json=auth_payload)
            logging.info(f"Auth Response Status: {response.status_code}")
            logging.info(f"Auth Response Content: {response.text}")

            response.raise_for_status()
            auth_data = response.json()

            if auth_data.get("Success"):
                logging.info("Authentication successful")
                return auth_data.get("Ticket")
            else:
                error_reason = auth_data.get('FailReason', 'Unknown error')
                logging.error(f"Authentication failed: {error_reason}")
                return None

        except Exception as e:
            logging.error(f"Authentication error: {str(e)}", exc_info=True)
            return None
    
    # отримання даних з ендпоінта ІТ-Е
    def get_data(self, Ticket):
        """Enhanced data retrieval with comprehensive logging"""
        logging.info("Fetching data...")
        try:
            headers = {"Ticket": Ticket}
            payload = {
                "ReceivingParams": {"ReceivingStrategy": "All"},
                "Limit": 400
            }
            
            logging.info(f"Data fetch payload: {payload}")
            
            response = requests.post(self.data_endpoint, headers=headers, json=payload)
            logging.info(f"Data Response Status: {response.status_code}")
            logging.info(f"Data Response Content: {response.text}")
            print(f"📌 response: {response}")

            response.raise_for_status()
            data = response.json()

            if data.get("IsSuccess"):
                logging.info(f"Retrieved {len(data['Data'])} records")
                return data["Data"]
            else:
                logging.error("Data retrieval failed")
                return None

        except Exception as e:
            logging.error(f"Data retrieval error: {str(e)}", exc_info=True)
            return None
    
    # запис/поновлення даних в Новшин
    def create_or_update_notion_page(self, item):
        """Create or update a Notion page with error handling for 502 responses"""
        logging.info(f"Processing Notion page for item: {item}")
        try:
            # Безпечне перетворення в число
            def safe_int(value, default=0):
                try:
                    return int(value)
                except (ValueError, TypeError):
                    return default

            # Властивості сторінки
            properties = {
                "Code": {"number": safe_int(item.get("Code"))},
                "Name": {"title": [{"text": {"content": str(item.get("Name", ""))}}]},
                # "BussinessUnitCode": {"rich_text": [{"text": {"content": str(item.get("BussinessUnitCode", ""))}}]},
                "BussinessUnitCodeITe": {"number": safe_int(item.get("BussinessUnitCodeITe"))},
                "BussinessUnitName": {"rich_text": [{"text": {"content": str(item.get("BussinessUnitName", ""))}}]},
                "DateFrom": {"date": {"start": item.get("DateFrom", "").split("T")[0]} if item.get("DateFrom") else None},
            }

            # Пошук сторінки з таким же Code
            filter_query = {
                "property": "Code",
                "number": {"equals": safe_int(item.get("Code"))}
            }
            attempt = 0
            max_retries = 3  # Максимальна кількість повторів у разі помилки

            while attempt < max_retries:
                try:
                    # Пошук існуючого запису
                    search_results = self.notion.databases.query(database_id=self.database_id, filter=filter_query)

                    if search_results["results"]:
                        # Оновлення існуючого запису
                        page_id = search_results["results"][0]["id"]
                        self.notion.pages.update(page_id=page_id, properties=properties)
                        logging.info(f"Updated existing Notion page for Code: {item.get('Code')}")
                    else:
                        # Створення нового запису
                        self.notion.pages.create(parent={"database_id": self.database_id}, properties=properties)
                        logging.info(f"Created new Notion page for Code: {item.get('Code')}")

                    return True  # Успіх, вихід з циклу
                except Exception as e:
                    if "502" in str(e):
                        logging.warning(f"502 error encountered for Code: {item.get('Code')}. Retrying...")
                        attempt += 1
                        time.sleep(2 ** attempt)  # Експоненціальне збільшення затримки
                    else:
                        raise  # Інші помилки не обробляємо в цьому циклі

            logging.error(f"Max retries exceeded for item {item.get('Code')}")
            return False

        except Exception as e:
            logging.error(f"Error processing Notion page for item {item.get('Code')}: {str(e)}", exc_info=True)
            return False


    def get_existing_notion_pages(self):
        """Retrieve all existing pages from the Notion database."""
        logging.info("Fetching existing Notion pages...")
        try:
            existing_pages = {}
            has_more = True
            start_cursor = None

            while has_more:
                response = self.notion.databases.query(
                    database_id=self.database_id,
                    start_cursor=start_cursor
                )
                for page in response["results"]:
                    properties = page["properties"]
                    code = properties["Code"]["number"]
                    existing_pages[code] = {
                        "id": page["id"],
                        "properties": properties,
                    }
                has_more = response.get("has_more", False)
                start_cursor = response.get("next_cursor")

            logging.info(f"Fetched {len(existing_pages)} existing pages from Notion.")
            return existing_pages

        except Exception as e:
            logging.error(f"Error fetching existing pages: {str(e)}", exc_info=True)
            return {}

    # Новий метод для перевірки змін
    def has_changes(self, existing_properties, new_properties):
        """Check if there are changes between existing and new properties."""
        def get_existing_value(properties, key):
            if key not in properties:
                return None
            prop = properties[key]
            if "number" in prop:
                return prop["number"]
            if "title" in prop:
                return prop["title"][0]["text"]["content"] if prop["title"] else ""
            if "rich_text" in prop:
                return prop["rich_text"][0]["text"]["content"] if prop["rich_text"] else ""
            if "date" in prop and prop["date"]:
                return prop["date"]["start"]
            return None

        for key, new_value in new_properties.items():
            existing_value = get_existing_value(existing_properties, key)

            if key == "DateFrom" and existing_value is not None:
                existing_value = existing_value.split("T")[0]  # Убрати час, якщо є

            # Розпаковка складних форматів нових властивостей
            if "number" in new_value:
                new_value = new_value["number"]
            elif "title" in new_value:
                new_value = new_value["title"][0]["text"]["content"] if new_value["title"] else ""
            elif "rich_text" in new_value:
                new_value = new_value["rich_text"][0]["text"]["content"] if new_value["rich_text"] else ""
            elif "date" in new_value:
                new_value = new_value["date"]["start"]

            # Порівняння значень
            if str(existing_value) != str(new_value):
                return True
        return False

    # Оновлений метод sync_data
    def sync_data(self, login, password):
        """Enhanced data synchronization with change detection."""
        logging.info("Starting enhanced data synchronization...")

        ticket = self.authenticate(login, password)
        if not ticket:
            logging.error("Authentication failed")
            return False

        data = self.get_data(ticket)
        if not data:
            logging.error("No data retrieved")
            return False

        # Get existing pages in Notion
        existing_pages = self.get_existing_notion_pages()

        success_count = 0
        for item in data:
            code = int(item.get("Code", 0))
            new_properties = {
                "Code": {"number": code},
                "Name": {"title": [{"text": {"content": item.get("Name", "")}}]},
                "BussinessUnitCodeITe": {"number": int(item.get("BussinessUnitCodeITe", 0))},
                "BussinessUnitName": {"rich_text": [{"text": {"content": item.get("BussinessUnitName", "")}}]},
                "DateFrom": {"date": {"start": item.get("DateFrom", "").split("T")[0]} if item.get("DateFrom") else None},
            }

            if code in existing_pages:
                # Check for changes
                existing_properties = existing_pages[code]["properties"]
                if self.has_changes(existing_properties, new_properties):
                    # Update if changes are found
                    page_id = existing_pages[code]["id"]
                    try:
                        self.notion.pages.update(page_id=page_id, properties=new_properties)
                        logging.info(f"Updated page for Code: {code}")
                    except Exception as e:
                        logging.error(f"Failed to update page for Code {code}: {str(e)}")
                else:
                    logging.info(f"No changes detected for Code: {code}")
            else:
                # Create new page
                try:
                    self.notion.pages.create(parent={"database_id": self.database_id}, properties=new_properties)
                    logging.info(f"Created new page for Code: {code}")
                except Exception as e:
                    logging.error(f"Failed to create page for Code {code}: {str(e)}")

            success_count += 1

        logging.info(f"Sync completed. Successfully processed: {success_count}/{len(data)}")
        return True