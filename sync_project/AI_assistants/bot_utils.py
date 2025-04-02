import sys
import os
import logging
import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, Document, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ConversationHandler, MessageHandler, filters
from urllib import response

# Додаємо кореневу директорію проекту до Python path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sync_project.settings')
import django

django.setup()
from AI_assistants.models import TrainingMaterial, ChatHistory
from nontion_sync.models import Project, NotionOrders, AIgenTask, Parent
# from AI_assistants.tasks import send_task_reminders
from django.db import models
from django.db.models import QuerySet
from asgiref.sync import sync_to_async
import pandas as pd
from googleapiclient.discovery import build
from docx import Document as DocxDocument
from PyPDF2 import PdfReader
import openai
from telegram.ext import CallbackContext
from django.conf import settings
from AI_assistants.models import Tok, ChanellAndTopik
from django.db import transaction
from typing import List, Dict, Tuple, Any
import hashlib
from telegram import Bot
import asyncio
# Налаштування логування
log_dir = os.path.dirname(os.path.abspath(__file__))
log_file = os.path.join(log_dir, 'notion_sync.log')
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(log_file)
    ]
)
logger = logging.getLogger("notion_sync")
CHUNK_SIZE = 3000
MAX_CHUNKS = 5
name = "AI asist fot PM"
tok_instance = Tok.objects.filter(name=name).first()
BOT_TOKEN = tok_instance.telegram_id
OPENAI_API_KEY = tok_instance.gpt_id

async def send_message_to_channel(channel_id, message):
    """Асинхронно надсилає повідомлення в канал без топіка"""
    bot = Bot(token=BOT_TOKEN)

    try:
        await bot.send_message(
            chat_id=channel_id,
            text=message,
            parse_mode="Markdown"
        )
        logger.info(f"✅ Повідомлення успішно відправлено в {channel_id} без топіка")
    except Exception as e:
        logger.error(f"❌ Помилка надсилання в {channel_id} без топіка: {e}")

async def send_message_to_topic(topic_id, message, channel_id):
    """Асинхронно надсилає повідомлення в конкретний топік Telegram-групи"""
    bot = Bot(token=BOT_TOKEN)

    try:
        await bot.send_message(
            chat_id=channel_id,
            text=message,
            parse_mode="Markdown",
            message_thread_id=topic_id
        )
        logger.info(f"✅ Повідомлення успішно відправлено в {channel_id} (топік {topic_id})")
    except Exception as e:
        logger.error(f"❌ Помилка надсилання в {channel_id} (топік {topic_id}): {e}")

def send_message_to_channel_sync(channel_id, message):
    """Синхронний виклик для надсилання повідомлення в канал без топіка"""
    import asyncio
    asyncio.run(send_message_to_channel(channel_id, message))

def send_message_to_topic_sync(topic_id, message, channel_id):
    """Синхронний виклик для надсилання повідомлення з топіком"""
    import asyncio
    asyncio.run(send_message_to_topic(topic_id, message, channel_id))