import json
from multiprocessing import context
import sys
import os
import logging
import asyncio
from urllib import response
import requests
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, Document,ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ConversationHandler, MessageHandler, filters
# Додаємо кореневу директорію проекту до Python path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sync_project.settings')
import django

django.setup()
from AI_assistants.models import TrainingMaterial, ChatHistory, Tok
from nontion_sync.models import Project, NotionOrders, AIgenTask, Parent, Task
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
import tiktoken 
import time
import uuid
import re
from django.db import transaction
from typing import List, Dict, Tuple, Any
import hashlib

CHUNK_SIZE = 3000
MAX_CHUNKS = 10
name = "AI asist fot PM"
tok_instance = Tok.objects.filter(name=name).first()
BOT_TOKEN = tok_instance.telegram_id
OPENAI_API_KEY = tok_instance.gpt_id
logging.basicConfig(format="%(asctime)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)
user_requests_channel_post_reply = {}
BOT_USERNAME = "@MiragePandA_bot"  
AI_CONSULT_MODE = set()



bot_username = "@MiragePandA_bot"

GROUP_ID = -1002407037240  #  ID групи

async def handle_mention(update: Update, context: CallbackContext):
    """Обробляє повідомлення, якщо бота згадали у групі."""
    chat_id = update.message.chat.id
    if chat_id == GROUP_ID:  # Перевіряємо, що повідомлення з потрібної групи
        text = update.message.text
        bot_username = (await context.bot.get_me()).username

        if f"@{bot_username}" in text:
            user_question = text.replace(f"@{bot_username}", "").strip()

            if not user_question:
                await update.message.reply_text("Привіт! Чим можу допомогти?")
            else:
                response = await ask_gpt_analysis(user_question)
                await update.message.reply_text(response)

async def send_menu_to_channel(update: Update, context: CallbackContext):
    """Відправляє меню в канал."""
    keyboard = [
        [InlineKeyboardButton("📄 Завантажити ТЗ", callback_data="upload_tz")],
        [InlineKeyboardButton("📚 Завантажити навч. мат.", callback_data="upload_material")],
        [InlineKeyboardButton("🤖 Консультація з AI", callback_data="consult_ai")],
        [InlineKeyboardButton("🎯 Написати SMART-цілі", callback_data="smart_goals")],
        # [InlineKeyboardButton("📝 Згенерувати таски", callback_data="generate_tasks")],
        [InlineKeyboardButton("📂 Сформувати файл з ордерами", callback_data="generate_orders_file")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    try:
        await context.bot.send_message(
            chat_id=update.message.chat.id,
            text="Привіт! Що вам потрібно?",
            reply_markup=reply_markup
        )
    except Exception as e:
        logging.error(f"Помилка при відправці меню в канал: {e}")

async def start(update: Update, context: CallbackContext):
    """Відправляє меню кнопок у приватному чаті або в каналі при натисканні 'Почати'."""
    keyboard = [
        [InlineKeyboardButton("📄 Завантажити ТЗ", callback_data="upload_tz")],
        [InlineKeyboardButton("📚 Завантажити навч. мат.", callback_data="upload_material")],
        [InlineKeyboardButton("🤖 Консультація з AI", callback_data="consult_ai")],
        [InlineKeyboardButton("🎯 Написати SMART-цілі", callback_data="smart_goals")],
        [InlineKeyboardButton("📝 Згенерувати таски", callback_data="generate_tasks")],
        [InlineKeyboardButton("📂 Сформувати файл з ордерами", callback_data="generate_orders_file")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    if update.message:
        await update.message.reply_text("Привіт! Що вам потрібно?", reply_markup=reply_markup)
    elif update.callback_query:
        await update.callback_query.message.edit_text("Що ви хочете зробити?", reply_markup=reply_markup)

async def handle_mention(update: Update, context: CallbackContext):
    """Обробляє повідомлення, якщо бота згадали у групі."""
    chat_id = update.message.chat.id
    if chat_id == GROUP_ID:  # Перевіряємо, що повідомлення з потрібної групи
        text = update.message.text
        bot_username = (await context.bot.get_me()).username

        if f"@{bot_username}" in text:
            user_question = text.replace(f"@{bot_username}", "").strip()

            if not user_question:
                await update.message.reply_text("Привіт! Чим можу допомогти?")
            else:
                response = await ask_gpt_analysis(user_question)
                await update.message.reply_text(response)


async def get_projects():
    return await sync_to_async(list)(Project.objects.all())


# Визначте стани для ConversationHandler
WAITING_PROJECT_NAME = 1
WAITING_FOR_DATE = 1
WAITING_FOR_TASKS = 1


async def create_new_project(update: Update, context: CallbackContext):
    await update.callback_query.answer()
    await update.callback_query.message.reply_text("Введіть назву нового проєкту:")
    return WAITING_PROJECT_NAME

async def handle_new_project_name(update: Update, context: CallbackContext):
    project_name = update.message.text
    try:
        new_project = await sync_to_async(Project.objects.create)(name=project_name)
        context.user_data["selected_project"] = new_project.id
        await update.message.reply_text(
            f"Проект '{project_name}' створено. Тепер завантажте ТЗ у форматі .docx, .pdf, .xlsx або .csv"
        )
    except Exception as e:
        logging.error(f"Error creating project: {e}")
        await update.message.reply_text("Виникла помилка при створенні проекту. Спробуйте ще раз.")
    return ConversationHandler.END


async def button_handler(update: Update, context):
    query = update.callback_query
    user_id = query.from_user.id  # Зберігаємо id користувача

    # Активуємо відповіді на пости для користувача
    if query.data == "activate_channel_reply":
        user_requests_channel_post_reply[user_id] = True
        await query.answer()
        await query.edit_message_text("Відповіді на пости в каналі активовано! Тепер бот може реагувати на ваші пости.")
    
    elif query.data == "bot_help_in_channel":
        # Інші варіанти кнопок для допомоги в каналі
        keyboard = [
            [InlineKeyboardButton("📄 Завантажити ТЗ", callback_data="upload_tz")],
            [InlineKeyboardButton("📚 Завантажити навч. мат.", callback_data="upload_material")],
            [InlineKeyboardButton("🤖 Консультація з AI", callback_data="consult_ai")],
            [InlineKeyboardButton("🎯 Написати SMART-цілі", callback_data="smart_goals")],
            [InlineKeyboardButton("📝 Згенерувати таски", callback_data="generate_tasks")],
            [InlineKeyboardButton("📂 Сформувати файл з ордерами", callback_data="generate_orders_file")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.message.reply_text("Виберіть дію, яку ви хочете виконати:", reply_markup=reply_markup)

    elif query.data == "upload_tz":
        projects = await get_projects()
        keyboard = [[InlineKeyboardButton(project.name, callback_data=f"project_{project.id}")] for project in projects]
        keyboard.append([InlineKeyboardButton("🆕 Створити новий проєкт", callback_data="create_new_project")])
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.message.reply_text("Виберіть існуючий проект або створіть новий:", reply_markup=reply_markup)
    
    elif query.data.startswith("project_"):
        project_id = int(query.data.split("_")[1])
        context.user_data["selected_project"] = project_id
        await query.message.reply_text("Тепер завантажте ТЗ у форматі .docx, .pdf, .xlsx, .csv")
    
    elif query.data == "create_new_project":
        await query.message.reply_text("Введіть назву нового проєкту:")

    elif query.data == "upload_material":
        await query.message.reply_text("Будь ласка, надішліть файл для навчального матеріалу.")    
    elif query.data == "consult_ai":
        await query.message.reply_text("Напишіть ваше питання, і я спробую вам допомогти!")
    
    elif query.data == "smart_goals":
        projects = await get_projects()
        keyboard = [[InlineKeyboardButton(project.name, callback_data=f"smart_goals_project_{project.id}")] for project in projects]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.message.reply_text("Виберіть проект для створення SMART-цілей:", reply_markup=reply_markup)

    elif query.data == "generate_orders_file":
        await query.message.reply_text("Введіть місяць і рік у форматі MM.YYYY (наприклад, 01.2025):")
        return WAITING_FOR_DATE
        return WAITING_FOR_DATE
    
    elif query.data == "generate_tasks":
        logging.info("Користувач натиснув кнопку 'Згенерувати таски'")
        projects = await get_projects()
        logging.info(f"Знайдено {len(projects)} проектів")
        if not projects:
            await query.message.reply_text("Немає доступних проектів.")
            return
    
        keyboard = [[InlineKeyboardButton(project.name, callback_data=f"tasks_project_{project.id}")] for project in projects]
        reply_markup = InlineKeyboardMarkup(keyboard)
    
        logging.info("Повідомлення з вибором проекту відправлено")
        await query.message.reply_text("Виберіть проект для генерації тасок:", reply_markup=reply_markup)
    elif query.data.startswith("tasks_project_"):
        logging.info(f"Отримано callback: {query.data}")  # Має вивести tasks_project_123
        project_id = int(query.data.split("_")[-1])
        logging.info(f"Обраний проект: {project_id}")

        # Додати перевірку чи є ТЗ
        if await project_has_tz(project_id):
            logging.info("Проект має ТЗ, починаємо генерацію тасок")
            await handle_tasks_project(project_id, update, context)  # Замінити на правильну функцію
        else:
            logging.info("Цей проект не має ТЗ")
            await query.answer()
            await query.message.reply_text("Цей проект не має технічного завдання (ТЗ), тому не можна створити задачі.")

    


# Формування Ексель файла з ордерами
async def handle_date_input(update: Update, context):
    user_input = update.message.text.strip()

    # Очистка зайвих пробілів та перевірка формату
    user_input = user_input.replace(" ", "")
    
    if not user_input or len(user_input) != 7 or user_input[2] != ".":
        await update.message.reply_text("❌ Невірний формат. Введіть у форматі MM.YYYY (наприклад, 01.2025). Спробуйте ще раз.")
        return WAITING_FOR_DATE

    try:
        month, year = map(int, user_input.split("."))
        if not (1 <= month <= 12):
            raise ValueError("Невірний формат місяця.")
    except ValueError:
        await update.message.reply_text("❌ Невірний формат. Введіть у форматі MM.YYYY (наприклад, 01.2025). Спробуйте ще раз.")
        return WAITING_FOR_DATE

    # Пошук ордерів за вказаний місяць та рік
    orders = await sync_to_async(list)(NotionOrders.objects.filter(status="Done", finish_date__year=year, finish_date__month=month ))
    if not orders:
        await update.message.reply_text("❌ Даних за цей період немає.")
        return ConversationHandler.END

    # Формуємо Excel-файл
    file_path = await generate_orders_excel(orders, month, year)
    await update.message.reply_document(document=open(file_path, "rb"), filename=os.path.basename(file_path))
    return ConversationHandler.END

async def generate_orders_excel(orders, month, year):
   
    df = pd.DataFrame.from_records([
        {
            "Назва завдання": "Назва",
            "Назва замовлення (коротко у 1 реченні)": order.service_name,
            "Опис завдання": f"{order.description + ',' or ''} {order.url_docs or ''}".strip(),
            "Назва компанії, що замовляє послугу (уточни у свого СЕО)": order.business_project_pf,
            "Напрямок Netpeak Core": order.team,
            "Тип розподілу вартості послуг між компаніями NG": order.cost_allocation_type,
            "Розподіл вартості послуги між компанiями NG (комп. А - n%, комп. В - n%, etc...)": order.cost_allocation,
            "Дата розміщення замовлення": order.order_date.strftime("%d-%m-%Y") if order.finish_date else "",
            "Дата прийняття виконаної послуги": order.finish_date.strftime("%d-%m-%Y") if order.finish_date else "",
            "Відповідальний виконавець замовлення": order.get_responsible_pf_display(),
            "Кількість замовлених послуг / годин роботи над замовленням": order.hours_unit,
            "Коментарі виконавця до замовлення": order.order_id_num,
            "Статус": "Завершене" if order.status == "Done" else order.status,
            "Назва послуги": order.service_name,
            "Категорія послуги": order.category,
            "Вартість замовлення": order.order_cost,
            "Посилання на Docs": order.url_docs
            
        } for order in orders
    ])
    
    file_path = f"orders_{month:02d}_{year}.xlsx"
    df.to_excel(file_path, index=False)
    return file_path


async def handle_document(update: Update, context):
    document = update.message.document
    file = await context.bot.get_file(document.file_id)

    # Створюємо папку для збереження файлів
    download_folder = os.path.join(os.getcwd(), "downloads")
    os.makedirs(download_folder, exist_ok=True)

    # Шлях до файлу
    file_path = os.path.join(download_folder, document.file_name)

    # Завантаження файлу
    await file.download_to_drive(file_path)

    # Парсимо документ
    extracted_text = await sync_to_async(parse_document)(file_path, document.file_name)

    # Якщо файл Excel/CSV, конвертуємо в JSON
    if document.file_name.endswith(".xlsx") or document.file_name.endswith(".csv"):
        extracted_text = f"Ось дані у форматі JSON:\n{extracted_text}"

    # Обрізаємо текст, якщо він занадто великий
    MAX_TOKENS = 15000  # Резерв залишаємо для відповіді AI
    extracted_text = extracted_text[:MAX_TOKENS]  

    # Отримуємо ID користувача Telegram
    telegram_user_id = str(update.message.from_user.id)

    # Визначаємо, чи це ТЗ чи навчальний матеріал
    if "selected_project" in context.user_data:
        project_id = context.user_data["selected_project"]
        direction = "project"
    else:
        project_id = None
        direction = "general"

    # Збереження в базу
    await sync_to_async(TrainingMaterial.objects.create)(
        name=document.file_name,
        direction=direction,
        content=extracted_text,
        telegram_user_id=telegram_user_id,
        project_id=project_id,
    )

    # Відправка відповіді користувачу
    if direction == "project":
        await update.message.reply_text("ТЗ збережено. AI аналізує документ...")
        chat_id = update.effective_chat.id
        AI_CONSULT_MODE.add(chat_id)
        # Розбиваємо великий текст на частини
        chunk_size = 4000  # Максимальна довжина одного запиту до GPT
        chunks = [extracted_text[i:i+chunk_size] for i in range(0, len(extracted_text), chunk_size)]

        analysis_results = []
        for chunk in chunks:
            analysis = await analyze_tz_with_ai(chunk)
            analysis_results.append(analysis)

        # Збираємо підсумковий аналіз
        final_analysis = "\n\n".join(analysis_results)
        await save_chat_history(chat_id, analysis_results, final_analysis)
        await update.message.reply_text(f"AI враження:\n{final_analysis[:4000]}")  # GPT має обмеження на довжину відповіді

    else:
        await update.message.reply_text("Навчальний матеріал успішно збережено! ✅")



async def enable_ai_consult(update: Update, context: CallbackContext):
    """Активує режим консультації AI після натискання кнопки."""
    chat_id = update.effective_chat.id
    AI_CONSULT_MODE.add(chat_id)  # Додаємо чат у список консультації

    await update.callback_query.message.reply_text(
        "✅ Ви активували режим консультації AI.\n\n"
        "Напишіть запит, і я відповім вам."
    )

async def handle_ai_consult(update: Update, context: CallbackContext):
    """Обробляє повідомлення користувача для AI консультації."""
    chat_id = update.effective_chat.id
    user_text = update.message.text if update.message else update.channel_post.text

    # Отримуємо ім'я бота
    bot_username = (await context.bot.get_me()).username
    mentioned = f"@{bot_username}" in user_text if user_text else False

    # У приватних чатах і в режимі консультації — відповідаємо завжди
    if update.effective_chat.type == "private" or chat_id in AI_CONSULT_MODE:
        AI_CONSULT_MODE.add(chat_id)
        should_respond = True
    else:
        # У групах відповідаємо тільки якщо є згадка
        should_respond = mentioned

    if should_respond:
        # Отримуємо останню історію повідомлень (обмеження в 10 останніх)
        context_history = await get_recent_context(chat_id, limit=10)
        if len(context_history) > 5000:
            context_history = context_history[-4000:]

        # Формуємо запит із контекстом
        full_prompt = f"{context_history}\nUser: {user_text}\nAI:"
        response = await ask_gpt_analysis(full_prompt)
        await save_chat_history(chat_id, user_text, response)
        await update.effective_message.reply_text(response)

def parse_document(file_path, file_name):
    if file_name.endswith(".docx"):
        doc = DocxDocument(file_path)
        return "\n".join([p.text for p in doc.paragraphs])
    elif file_name.endswith(".pdf"):
        reader = PdfReader(file_path)
        return "\n".join([page.extract_text() for page in reader.pages])
    elif file_name.endswith(".xlsx") or file_name.endswith(".csv"):
        df = pd.read_excel(file_path) if file_name.endswith(".xlsx") else pd.read_csv(file_path)
        return df.to_json(orient="records", force_ascii=False)
   
    return "Невідомий формат"



async def analyze_tz_with_ai(text):
    max_tokens = 3000  # Ліміт токенів на запит
    encoding = tiktoken.encoding_for_model("gpt-3.5-turbo")  # Використовуємо токенізатор OpenAI

    paragraphs = text.split("\n")  # Розбиваємо текст на абзаци
    parts = []
    current_part = []
    current_tokens = 0

    for paragraph in paragraphs:
        paragraph_tokens = len(encoding.encode(paragraph))  # Рахуємо токени в абзаці

        if current_tokens + paragraph_tokens > max_tokens:
            if current_part:
                parts.append("\n".join(current_part))  # Зберігаємо поточну частину
            current_part = [paragraph]  # Починаємо нову частину
            current_tokens = paragraph_tokens
        else:
            current_part.append(paragraph)
            current_tokens += paragraph_tokens

    if current_part:
        parts.append("\n".join(current_part))  # Додаємо останню частину

    # Надсилаємо частини до GPT і збираємо результати
    results = []
    for part in parts:
        response = await ask_gpt_analysis(part)
        results.append(response)

    return "\n\n".join(results)


async def ask_gpt_analysis(question):
    openai.api_key = OPENAI_API_KEY
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "Ти – досвідчений проєктний менеджер і фінансовий бізнес-аналітик. Твоя основна мета – допомагати користувачам у плануванні, аналізі та управлінні проєктами. Ти аналізуєш технічні завдання (ТЗ), формуєш SMART-цілі, пропонуєш оптимальні підходи до управління ресурсами, оцінюєш фінансові ризики та ефективність рішень.Коли користувач ставить запитання, надай чітку, структуровану та практичну відповідь. Використовуй методики управління проєктами (PMBOK, Agile, Scrum, Kanban) та фінансовий аналіз (ROI, NPV, фінансове моделювання). Якщо аналізуєш ТЗ, звертай увагу на:✅ Логіку, узгодженість і чіткість вимог, ✅ Відповідність SMART-цілям, ✅ Фінансову доцільність та ризики реалізації. Відповідай стисло, без зайвої води, орієнтуючись на практичні рекомендації. Якщо потрібен розширений аналіз – запитуй додаткову інформацію.."},
            {"role": "user", "content": question}
        ]
    )
    return response["choices"][0]["message"]["content"].strip()


# Функція для отримання проекту за ID
@sync_to_async
def get_tz_for_project(project_id: int):
    try:
        return list(TrainingMaterial.objects.filter(project_id=project_id))
    except Exception as e:
        logging.error(f"Error getting TZ for project {project_id}: {e}")
        return []

@sync_to_async
def get_project_by_id(project_id: int):
    try:
        return Project.objects.get(id=project_id)
    except Project.DoesNotExist:
        return None
    except Exception as e:
        logging.error(f"Error getting project {project_id}: {e}")
        return None

# Функція для перевірки наявності ТЗ для проекту
async def project_has_tz(project_id: int) -> bool:
    logging.info(f"Отримуємо ТЗ для проекту {project_id}")
    tz_list = await get_tz_for_project(project_id)
    return len(tz_list) > 0

# Функція для отримання тасок за проектом
@sync_to_async
def get_tasks_for_project(project_id: int):
    try:
        project = Project.objects.get(id=project_id)  # Отримуємо проект за Django ID
        project_id_str = project.project_id  # Отримуємо `project_id` з моделі
        logging.info(f"Шукаємо таски для project_id: '{project_id_str}'")

        tasks = list(Task.objects.filter(project=project_id_str))  # Фільтруємо по `project_id`

        logging.info(f"Знайдено {len(tasks)} тасок для project_id '{project_id_str}'")
        return tasks
    except Project.DoesNotExist:
        logging.error(f"Проект з id {project_id} не знайдено")
        return []
    except Exception as e:
        logging.error(f"Error getting tasks for project {project_id}: {e}")
        return []

# Основний хендлер для SMART цілей
async def smart_goals_handler(update: Update, context: CallbackContext):
    if update.callback_query:
        user_id = update.callback_query.from_user.id
        callback_data = update.callback_query.data

        if callback_data.startswith('smart_goals_project_'):
            project_id = int(callback_data.split('_')[-1])
            tz_exists = await project_has_tz(project_id)
            tasks = await get_tasks_for_project(project_id)
            print(f"Проект {project_id}: ТЗ існує - {tz_exists}, таски - {tasks}")

            if tasks:
                await context.bot.send_message(user_id, f"Знайдено {len(tasks)} завдань для проекту.")
            else:
                await context.bot.send_message(user_id, "Завдань для цього проекту немає.")
            if tz_exists or tasks:
                await update.callback_query.answer()
                await handle_smart_goals_for_project(project_id, update, context)
            else:
                await update.callback_query.answer()
                await context.bot.send_message(
                    user_id, 
                    "Цей проект не має технічного завдання (ТЗ) або завдань, тому не можна створити SMART цілі."
                )
    
    elif update.message:
        user_id = update.message.from_user.id
        projects = await sync_to_async(list)(Project.objects.all())
        keyboard = [
            [InlineKeyboardButton(project.name, callback_data=f"smart_goals_project_{project.id}")] 
            for project in projects
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(
            "Виберіть проект для написання SMART цілей:", 
            reply_markup=reply_markup
        )


# Функція для обробки SMART цілей для вибраного проекту
async def handle_smart_goals_for_project(project_id: int, update: Update, context: CallbackContext):
    chat_id = update.effective_chat.id
    project = await get_project_by_id(project_id)
    if not project:
        await update.callback_query.message.reply_text("Проект не знайдений.")
        return

    tz_list = await get_tz_for_project(project_id)
    tasks_list = await get_tasks_for_project(project_id)

    if not tz_list and not tasks_list:
        await update.callback_query.message.reply_text(
            "Для цього проєкту немає ТЗ або тасок. Завантажте ТЗ або додайте таски для продовження."
        )
        return

    # Об'єднуємо текст з кількох ТЗ
    extracted_text = "\n\n".join([tz.content for tz in tz_list])

    # Додаємо таски до тексту
    if tasks_list:
        extracted_text += "\n\nЗавдання:\n"
        extracted_text += "\n".join([
            f"- {task.name} (Статус: {task.status}, Виконавець: {task.person}, Фініш: {task.finish})"
            for task in tasks_list
        ])

    logging.info(f"Отримані дані (перші 200 символів): {extracted_text[:200]}")

    # Формулюємо SMART-цілі
    chunk_size = 3000  # Оптимальний розмір для GPT
    max_chunks = 5  # Обмежимо до 5 частин
    chunks = [extracted_text[i:i+chunk_size] for i in range(0, min(len(extracted_text), chunk_size * max_chunks), chunk_size)]
    smart_goals_parts = []

    await update.callback_query.message.reply_text("Зачекайте, аналізую інформацію для написання SMART-цілей.")

    for i, chunk in enumerate(chunks):
        logging.info(f"Обробляємо частину {i+1}/{len(chunks)}...")

        start_time = time.time()
        smart_goals = await generate_smart_goals(chunk)
        elapsed_time = time.time() - start_time

        logging.info(f"Частина {i+1} оброблена за {elapsed_time:.2f} сек.")
        smart_goals_parts.append(smart_goals)

        await asyncio.sleep(0.5)  # Додаємо паузу між запитами

    final_smart_goals = "\n\n".join(smart_goals_parts)
    logging.info(f"Згенеровані SMART-цілі (перші 200 символів): {final_smart_goals[:200]}")

    await save_chat_history(chat_id, extracted_text, final_smart_goals)
    await update.callback_query.message.reply_text(
        f"SMART цілі для проєкту '{project.name}':\n\n{final_smart_goals[:4000]}"  # Ліміт у Telegram
    )
    

# Функція для генерації SMART цілей через GPT
async def generate_smart_goals(tz_text):
    prompt = f"""
    Проаналізуй наступне Технічне Завдання (ТЗ) і сформулюй SMART цілі:

    ТЗ: {tz_text}

    Поясни, які конкретні SMART цілі можна визначити з цього ТЗ. 
    Кожна окрема SMART ціль повинна вкльчати в себе:
    - Specific (конкретні)
    - Measurable (вимірні)
    - Achievable (досяжні)
    - Relevant (релевантні)
    - Time-bound (строкові)
    """
    smart_goals_response = await ask_gpt(prompt)
    return smart_goals_response

# Функція для запиту до GPT
async def ask_gpt(prompt: str) -> str:
    openai.api_key = OPENAI_API_KEY
    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "Ти - експерт з формування SMART цілей на основі технічних завдань."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=1000
        )
        return response.choices[0].message.content
    except Exception as e:
        logging.error(f"Error with GPT request: {e}")
        return "Виникла помилка при запиті до GPT. Спробуйте ще раз."


# Збереження контексту розмови з АІ асистентом
async def save_chat_history(user_id, user_message, ai_response):
    session_id = str(uuid.uuid4())  # Генеруємо унікальний ID для сесії (можна групувати за часом)
    
    await sync_to_async(ChatHistory.objects.create)(
        user_id=user_id,
        session_id=session_id,
        message=user_message,
        response=ai_response
    )

def get_chat_history(user_id, limit=10):
    return ChatHistory.objects.filter(user_id=user_id).order_by('-timestamp')[:limit]

async def get_recent_context(user_id, limit=8):
     """Асинхронно отримує останні повідомлення користувача для контексту AI."""
     history = await sync_to_async(
        lambda: list(ChatHistory.objects.filter(user_id=user_id).order_by('-timestamp')[:limit])
    )()
     context = "\n".join([f"User: {h.message}\nAI: {h.response}" for h in reversed(history)])
     return context



# Генерація АІ тасок для проектів по ТЗ

async def task_handler(update: Update, context: CallbackContext):
    logging.info(f"Обробляємо задачі для проекту {project_id}")
    if update.callback_query:
        user_id = update.callback_query.from_user.id
        callback_data = update.callback_query.data
        logging.info(f"Callback data отримано: {callback_data}")

        if callback_data.startswith('tasks_project_'):
            project_id = int(callback_data.split('_')[-1])

            if await project_has_tz(project_id):
                await update.callback_query.answer()
                await handle_tasks_project(project_id, update, context)
            else:
                await update.callback_query.answer()
                await context.bot.send_message(
                    user_id, 
                    "Цей проект не має технічного завдання (ТЗ), тому не можна створити Tasks."
                )
    
    elif update.message:
        user_id = update.message.from_user.id
        projects = await sync_to_async(list)(Project.objects.all())
        keyboard = [
            [InlineKeyboardButton(project.name, callback_data=f"tasks_project_{project.id}")] 
            for project in projects
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(
            "Виберіть проект для написання Tasks and parent tasks:", 
            reply_markup=reply_markup
        )

# Функція для обробки tasks для вибраного проекту
async def parse_and_save_tasks(project_id, tasks_text):
    """Асинхронна функція для збереження парентів та тасок"""
    await sync_to_async(_parse_and_save_tasks_sync)(project_id, tasks_text)

def _parse_and_save_tasks_sync(project_id, tasks_text):
    """Синхронна функція для збереження парентів та тасок"""
    with transaction.atomic():
        project = Project.objects.get(id=project_id)  # Отримуємо проєкт

        parent_blocks = re.split(r"\*\*Parent Task \d+:\*\*", tasks_text)[1:]

        for parent_text in parent_blocks:
            # Видаляємо зайві пробіли та переносимо на новий рядок
            parent_text = parent_text.strip()

            # Беремо перший рядок як назву парент таски
            lines = parent_text.split("\n")
            parent_title = lines[0].strip("* ").strip()

            # Зберігаємо парент у базу
            parent_task = Parent.objects.create(name=parent_title, project=project)

            # Витягуємо таски для цього парента
            task_matches = re.findall(r"- Task \d+: (.+?), (\d+) годин, #(\d+)", parent_text)

            for task_description, hours, task_id in task_matches:
                AIgenTask.objects.create(
                    name=task_description.strip(),  # Назва таски
                    parent_task=parent_task,  # Прив'язуємо до парента
                    project=project,  # Прив'язуємо до проєкту
                    hours_plan=float(hours),  # Якщо потрібно, можна парсити години окремо
                    status="Backlog",  # За замовчуванням статус
                    plan_cost=None,  # Якщо потрібно, можна парсити ціну окремо
                    order=int(task_id),  # Порядковий номер
                )

async def handle_tasks_project(project_id: int, update: Update, context: CallbackContext):
    chat_id = update.effective_chat.id
    project = await get_project_by_id(project_id)
    if not project:
        await update.callback_query.message.reply_text("Проект не знайдений.")
        return

    tz_list = await get_tz_for_project(project_id)
    if not tz_list:
        await update.callback_query.message.reply_text(
            "Для цього проєкту немає ТЗ. Завантажте ТЗ для продовження."
        )
        return

    # Об'єднуємо текст з кількох ТЗ
    extracted_text = "\n\n".join([tz.content for tz in tz_list])
    logging.info(f"Отриманий текст ТЗ: {extracted_text[:200]}")

    # Формулюємо tasks
    chunk_size = 4000  # Оптимальний розмір для GPT
    max_chunks = 5  # Обмежимо до 5 частин, щоб уникнути зависання
    chunks = [extracted_text[i:i+chunk_size] for i in range(0, min(len(extracted_text), chunk_size * max_chunks), chunk_size)]
    tasks_parts = []
    await update.callback_query.message.reply_text(
            "Зачекайте трішечки я аналізую інформацію для написання Тасок"
        )
    for i, chunk in enumerate(chunks):
        logging.info(f"Обробляємо частину {i+1}/{len(chunks)}...")
        
        start_time = time.time()
        tasks = await generate_tasks(chunk)
        elapsed_time = time.time() - start_time

        logging.info(f"Частина {i+1} оброблена за {elapsed_time:.2f} сек.")
        tasks_parts.append(tasks)

        await asyncio.sleep(0.5)  # Додаємо паузу між запитами, щоб уникнути навантаження

    final_tasks = "\n\n".join(tasks_parts)
    logging.info(f"Згенеровані таски (перші 200 символів): {final_tasks[:200]}")
    
    # await save_chat_history(chat_id, extracted_text, final_tasks)
    await parse_and_save_tasks(project_id, final_tasks)  # Збереження в базу
    await send_tasks_in_parts(chat_id, project.name, final_tasks, context)
    # await update.callback_query.message.reply_text(
    #     f"Ось таски для проєкту '{project.name}':\n\n{final_tasks[:4000]}"  # Ліміт у Telegram
    # )

async def send_tasks_in_parts(chat_id, project_name, tasks_text, context):
    """Розбиває список тасок на Parent Tasks і надсилає їх у Telegram"""
    
    parent_tasks = re.split(r"\*\*Parent Task \d+:", tasks_text)[1:]  # Розділяємо Parent Tasks
    logging.info(f"Кількість Parent Tasks: {len(parent_tasks)}")

    for idx, parent in enumerate(parent_tasks):
        message = f"**Parent Task {idx+1}:** {parent.strip()}"

        # Розбиваємо на частини, якщо довжина більше 4000 символів
        for part in [message[i:i+4000] for i in range(0, len(message), 4000)]:
            await context.bot.send_message(chat_id, part)
            await asyncio.sleep(1)  # Щоб уникнути ліміту запитів
    

# Функція для генерації tasks
async def generate_tasks(tz_text):
    prompt = f"""
    Ось технічне завдання (ТЗ) для проєкту. Виділи основні великі завдання (Parent Tasks) та дрібні кроки для кожного великого завдання (Tasks).
    Мінімальна кількість Parent Tasks 7 штук, максимальна 12 шт.
    Мінімальна кількість Tasks 150 штук. 

    порядковий номер таски в кінці назви таски є обовязковий так як планова кількість годин на виконання

    🔹 Формат відповіді:
    **Parent Task 1:** Назва великого завдання
        - Task 1: Опис, планова кількість годин на виконання, Порядковий номер таски
        - Task 2: Опис, планова кількість годин на виконання, Порядковий номер таски
        - Task N: Опис, Опис, планова кількість годин на виконання, Порядковий номер таски

        **Parent Task 2:** Назва великого завдання
        - Task 1: Опис, Опис, планова кількість годин на виконання, Порядковий номер таски
        - Task 2: Опис, Опис, планова кількість годин на виконання, Порядковий номер таски
        - Task N: Опис, Опис, планова кількість годин на виконання, Порядковий номер таски

    ТЗ: {tz_text}

    """
    smart_goals_response = await ask_gpt_tasks(prompt)
    return smart_goals_response

# Функція для запиту до GPT
async def ask_gpt_tasks(prompt: str) -> str:
    openai.api_key = OPENAI_API_KEY
    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "Ти - експерт з формування проектних тасок і парентів для них на основі технічних завдань. Мінімум тасок 150 штук"},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=4000
        )
        return response.choices[0].message.content
    except Exception as e:
        logging.error(f"Error with GPT request: {e}")
        return "Виникла помилка при запиті до GPT. Спробуйте ще раз."



def main():
    conv_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(create_new_project, pattern="^create_new_project$")],
        states={
            WAITING_PROJECT_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_new_project_name)]
        },
        fallbacks=[],
    )
    conv_handler_btn = ConversationHandler(
    entry_points=[CallbackQueryHandler(button_handler, pattern="^(?!smart_goals_project_).*")],
    states={
        WAITING_FOR_DATE: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_date_input)],
    },
    fallbacks=[],
)
    

    mention_handler = MessageHandler(filters.Mention([bot_username]), handle_mention)
    application = Application.builder().token(BOT_TOKEN).build()
    application.add_handler(conv_handler)
    application.add_handler(conv_handler_btn)
    # application.add_handler(conv_handler_tasks)
    application.add_handler(CommandHandler("start", start))
    # application.add_handler(CallbackQueryHandler(button_handler, pattern="^(?!smart_goals_project_).*"))
    
    application.add_handler(mention_handler)
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_ai_consult))
    application.add_handler(MessageHandler(filters.Document.ALL, handle_document))
    application.add_handler(CallbackQueryHandler(smart_goals_handler, pattern="^smart_goals_project_"))
    application.add_handler(CallbackQueryHandler(handle_smart_goals_for_project, pattern="^smart_goals_project_"))
    application.add_handler(CallbackQueryHandler(task_handler, pattern="^tasks_project_"))
    
    
    
    application.add_handler(MessageHandler(
        filters.TEXT & ~filters.COMMAND & ~filters.Regex("^.*$"), 
        handle_ai_consult
    ))
    application.add_handler(CallbackQueryHandler(enable_ai_consult, pattern="^consult_ai$"))
    # Обробник тільки згадок бота
    application.add_handler(MessageHandler(filters.TEXT & filters.Regex(f"{BOT_USERNAME}"), handle_mention))
    # Обробник постів у каналі
    application.add_handler(MessageHandler(filters.ChatType.CHANNEL, send_menu_to_channel))
    application.run_polling()

if __name__ == "__main__":
    main()