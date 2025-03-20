import sys
import os
import logging
import asyncio
from urllib import response
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, Document,ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ConversationHandler, MessageHandler, filters
# Додаємо кореневу директорію проекту до Python path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sync_project.settings')
import django

django.setup()
from AI_assistants.models import TrainingMaterial, ChatHistory
from nontion_sync.models import Project, NotionOrders, AIgenTask, Parent
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
from AI_assistants.models import Tok
from django.db import transaction
from typing import List, Dict, Tuple, Any
import hashlib
from telegram import Bot
import asyncio
CHUNK_SIZE = 3000
MAX_CHUNKS = 5
name = "AI asist fot PM"
tok_instance = Tok.objects.filter(name=name).first()
BOT_TOKEN = tok_instance.telegram_id
OPENAI_API_KEY = tok_instance.gpt_id
TELEGRAM_CHANNEL_ID = "-1002407037240"


async def send_message_to_topic(topic_id, message):
    """Асинхронно надсилає повідомлення в конкретний топік Telegram-групи"""
    if topic_id == 0:
        return  # Пропускаємо, якщо ID топіка не заданий

    bot = Bot(token=BOT_TOKEN)
    await bot.send_message(
        chat_id=TELEGRAM_CHANNEL_ID,  # Використовуємо заданий канал
        text=message,
        parse_mode="Markdown",
        message_thread_id=topic_id
    )

def send_message_to_topic_sync(topic_id, message):
    """Синхронний виклик для Celery"""
    asyncio.run(send_message_to_topic(topic_id, message))