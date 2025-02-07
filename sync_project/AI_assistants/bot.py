import sys
import os
import logging
import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, Document,ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ConversationHandler, MessageHandler, filters
# Додаємо кореневу директорію проекту до Python path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sync_project.settings')
import django

django.setup()
from AI_assistants.models import TrainingMaterial
from nontion_sync.models import Project, NotionOrders
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

BOT_TOKEN = settings.BOT_TOKEN
OPENAI_API_KEY = settings.OPENAI_API_KEY
logging.basicConfig(format="%(asctime)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

async def start(update: Update, context: CallbackContext):
    keyboard = [
        [InlineKeyboardButton("📄 Завантажити ТЗ", callback_data="upload_tz")],
        [InlineKeyboardButton("📚 Завантажити навч. мат.", callback_data="upload_material")],
        [InlineKeyboardButton("🤖 Консультація з AI", callback_data="consult_ai")],
        [InlineKeyboardButton("🎯 Написати SMART-цілі", callback_data="smart_goals")],
        [InlineKeyboardButton("📂 Сформувати файл з ордерами", callback_data="generate_orders_file")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Привіт! Що вам потрібно?", reply_markup=reply_markup)


async def get_projects():
    return await sync_to_async(list)(Project.objects.all())


# Визначте стани для ConversationHandler
WAITING_PROJECT_NAME = 1
WAITING_FOR_DATE = 1

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
    await query.answer()
    
    if query.data == "upload_tz":
        # await query.message.reply_text("Введіть назву проєкту або виберіть зі списку.")
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
    orders = await sync_to_async(list)(NotionOrders.objects.filter(finish_date__year=year, finish_date__month=month))
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
            "Назва завдання": order.name,
            "Назва замовлення": order.service_name,
            "Опис завдання": order.description,
            "Назва компанії, що замовляє послугу": order.business_unit,
            "Напрямок Netpeak Core": order.team,
            "Тип розподілу вартості послуг між компаніями NG": order.cost_allocation_type,
            "Розподіл вартості послуги між компанiями NG": order.cost_allocation,
            "Дата прийняття виконаної послуги": order.finish_date.strftime("%d.%m.%Y") if order.finish_date else "",
            "Відповідальний виконавець замовлення": order.responsible,
            "Кількість замовлених послуг / годин роботи над замовленням": order.hours_unit,
            "Статус": order.status
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

    # Правильний шлях до файлу
    file_path = os.path.join(download_folder, document.file_name)

    # Завантаження файлу
    await file.download_to_drive(file_path)

    # Виклик parse_document без await (бо це синхронна функція)
    extracted_text = await sync_to_async(parse_document)(file_path, document.file_name)

    # Отримуємо ID користувача Telegram
    telegram_user_id = str(update.message.from_user.id)

    # Перевіряємо, чи вибрано проєкт (якщо є, це ТЗ, якщо ні — навчальний матеріал)
    if "selected_project" in context.user_data:
        project_id = context.user_data["selected_project"]
        direction = "project"
    else:
        project_id = None
        direction = "general"

    # Збереження в базу
    await sync_to_async(TrainingMaterial.objects.create)(
        name=document.file_name,  # Назва документа
        direction=direction,  # "project" або "general"
        content=extracted_text,  # Текст
        telegram_user_id=telegram_user_id,  # ID користувача Telegram
        project_id=project_id,  # ID проєкту або None
    )

    # Відповідь користувачу
    if direction == "project":
        await update.message.reply_text("ТЗ збережено. AI аналізує документ...")
        analysis = await analyze_tz_with_ai(extracted_text)
        await update.message.reply_text(f"AI враження: {analysis}")
    else:
        await update.message.reply_text("Навчальний матеріал успішно збережено! ✅")



async def handle_ai_consult(update: Update, context):
    user_question = update.message.text
    response = await ask_gpt_analysis(user_question)
    await update.message.reply_text(response)


def parse_document(file_path, file_name):
    if file_name.endswith(".docx"):
        doc = DocxDocument(file_path)
        return "\n".join([p.text for p in doc.paragraphs])
    elif file_name.endswith(".pdf"):
        reader = PdfReader(file_path)
        return "\n".join([page.extract_text() for page in reader.pages])
    elif file_name.endswith(".xlsx") or file_name.endswith(".csv"):
        df = pd.read_excel(file_path) if file_name.endswith(".xlsx") else pd.read_csv(file_path)
        return df.to_string()
    return "Невідомий формат"


# Функція для аналізу ТЗ з розбиттям на частини
async def analyze_tz_with_ai(text):
    max_tokens = 4000  # Максимальна кількість токенів на запит до GPT
    paragraphs = text.split("\n")  # Розбиваємо ТЗ по абзацах
    parts = []
    current_part = []

    # Розбиваємо текст на частини, щоб кожна частина не перевищувала ліміт
    for paragraph in paragraphs:
        current_part.append(paragraph)
        if len(" ".join(current_part)) > max_tokens:
            parts.append(" ".join(current_part[:-1]))  # Додаємо попередню частину
            current_part = [paragraph]  # Починаємо нову частину

    if current_part:
        parts.append(" ".join(current_part))  # Додаємо останню частину

    # Надсилаємо частини до GPT і збираємо результати
    results = []
    for part in parts:
        response = await ask_gpt_analysis(part)
        results.append(response)

    # Об'єднуємо всі результати
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
    tz_list = await get_tz_for_project(project_id)
    return len(tz_list) > 0

# Основний хендлер для SMART цілей
async def smart_goals_handler(update: Update, context: CallbackContext):
    if update.callback_query:
        user_id = update.callback_query.from_user.id
        callback_data = update.callback_query.data

        if callback_data.startswith('smart_goals_project_'):
            project_id = int(callback_data.split('_')[-1])

            if await project_has_tz(project_id):
                await update.callback_query.answer()
                await handle_smart_goals_for_project(project_id, update, context)
            else:
                await update.callback_query.answer()
                await context.bot.send_message(
                    user_id, 
                    "Цей проект не має технічного завдання (ТЗ), тому не можна створити SMART цілі."
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

    # Формулюємо SMART-цілі
    smart_goals = await generate_smart_goals(extracted_text)
    logging.info(f"Згенеровані SMART-цілі: {smart_goals[:200]}")
    
    await update.callback_query.message.reply_text(
        f"SMART цілі для проєкту '{project.name}':\n\n{smart_goals}"
    )

# Функція для генерації SMART цілей через GPT
async def generate_smart_goals(tz_text):
    prompt = f"""
    Проаналізуй наступне Технічне Завдання (ТЗ) і сформулюй SMART цілі:

    ТЗ: {tz_text}

    Поясни, які конкретні SMART цілі можна визначити з цього ТЗ. 
    Цілі повинні бути:
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

    application = Application.builder().token(BOT_TOKEN).build()
    application.add_handler(conv_handler)
    application.add_handler(conv_handler_btn)
    application.add_handler(CommandHandler("start", start))
    # application.add_handler(CallbackQueryHandler(button_handler, pattern="^(?!smart_goals_project_).*"))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_ai_consult))
    application.add_handler(MessageHandler(filters.Document.ALL, handle_document))
    application.add_handler(CallbackQueryHandler(smart_goals_handler, pattern="^smart_goals_project_"))
    application.add_handler(CallbackQueryHandler(handle_smart_goals_for_project, pattern="^smart_goals_project_"))
    application.add_handler(MessageHandler(
        filters.TEXT & ~filters.COMMAND & ~filters.Regex("^.*$"), 
        handle_ai_consult
    ))
    application.run_polling()

if __name__ == "__main__":
    main()