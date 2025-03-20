import requests
import logging
import json
from AI_assistants.models import Tok

name = "AI asist fot PM"
tok_instance = Tok.objects.filter(name=name).first()
BOT_TOKEN = tok_instance.telegram_id

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

def get_last_topic():
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/getUpdates"
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()

        logging.info(f"Response: {json.dumps(data, indent=4, ensure_ascii=False)}")

        if "result" in data and data["result"]:
            last_message = None
            for update in reversed(data["result"]):  # Беремо останнє повідомлення
                if "message" in update and "chat" in update["message"]:
                    last_message = update["message"]
                    break  # Виходимо після першого знайденого (останнього) повідомлення

            if last_message:
                chat_id = last_message["chat"]["id"]
                thread_id = last_message.get("message_thread_id")  # Отримуємо ID топіка
                text = last_message.get("text", "Немає тексту")

                logging.info(f"Group Chat ID: {chat_id}")
                if thread_id:
                    logging.info(f"Last Topic ID: {thread_id}")
                else:
                    logging.info("Message is not from a topic (thread).")

                logging.info(f"Last Message: {text}")

                return chat_id, thread_id, text
        else:
            logging.warning("No chat or topic ID found. Try sending a message to the bot in the required topic.")

    except requests.RequestException as e:
        logging.error(f"Error fetching updates: {e}", exc_info=True)

get_last_topic()
