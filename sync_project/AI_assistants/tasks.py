import logging
from django.utils.timezone import now
from celery import chain
from sync_project.celery import app
from nontion_sync.models import Task
from nontion_sync.tasks import execute_projects_tasks
from AI_assistants.models import ChanellAndTopik
from AI_assistants.bot_utils import send_message_to_topic_sync, send_message_to_channel_sync

logger = logging.getLogger(__name__)

@app.task
def send_task_reminders():
    """Формує список тасок і повертає масив повідомлень для Telegram-топіків по проєктах."""
    active_statuses = ["In progress", "To Do", "Need fix", "Review"]
    tasks = Task.objects.filter(status__in=active_statuses).order_by("project", "person", "finish")

    if not tasks.exists():
        return []  # Немає тасок для повідомлення

    grouped_tasks = {}

    # Групуємо таски за проектом та користувачем
    for task in tasks:
        if not task.person or task.person.strip() == "Unknown Person":
            continue  # Пропускаємо таски з невідомим виконавцем

        project = ChanellAndTopik.objects.filter(project_external_id=task.project).first()  # Отримуємо об'єкт проєкту
        
        if not project:
            continue  # Пропускаємо таски без проєкту або без топіка

        if project.project_external_id not in grouped_tasks:
            grouped_tasks[project.project_external_id] = {}

        if task.person not in grouped_tasks[project.project_external_id]:
            grouped_tasks[project.project_external_id][task.person] = []

        overdue = "🔴 Прострочена" if task.finish and task.finish < now().date() else "🟢 В межах графіку"

        task_name_with_link = f"[{task.name}]({task.task_url})" if task.task_url else task.name

        grouped_tasks[project.project_external_id][task.person].append(
            f"📌 {task_name_with_link} (🕒 {task.hours_plan or 0} год / DDL {task.finish.strftime('%d.%m.%Y') if task.finish else '—'} / {task.status} / {overdue})"
        )

    # Створюємо масив повідомлень
    messages_array = []

    for project_external_id, users_tasks in grouped_tasks.items():
        # Отримуємо всі проекти для поточного external_id
        projects = ChanellAndTopik.objects.filter(project_external_id=project_external_id)
        print(projects)  # Для перевірки виводимо знайдені проекти

        # Якщо проекти не знайдені, переходимо до наступного external_id
        if not projects.exists():
            continue

        # Обробка кожного проекту для поточного project_external_id
        for project in projects:
            # Для кожного каналу створюємо повідомлення
            channel_id = project.channel_id
            print(channel_id)  # Для перевірки виводимо channel_id
            topic_id = project.topik_id if project.topik_id else 0  # Якщо топік є, використовуємо його, інакше 0

            # Формуємо повідомлення
            message = f"📢 *Планові таски по проєкту на поточний тиждень:* \n______\n"

            # Додаємо таски для кожної особи
            for person, task_list in users_tasks.items():
                message += f"\n👤 @{person}\n" + "\n".join(task_list) + "\n______\n"

            # Додаємо повідомлення в масив для цього каналу і топіка
            messages_array.append({
                "channel_id": channel_id,
                "topic_id": topic_id,  # Якщо топік є, додаємо його
                "message": message
            })

            # Логування згенерованого повідомлення
            logger.info(f"Згенеровано повідомлення для каналу {channel_id}, топіка {topic_id if topic_id else 'без топіка'}")

    # Далі обробка і надсилання повідомлень
    for msg in messages_array:
        channel_id = msg["channel_id"]
        topic_id = msg["topic_id"]
        message = msg["message"]

        # Якщо топік є, відправляємо з топіком
        if topic_id:
            send_message_to_topic_sync(topic_id, message, channel_id)
            logger.info(f"Повідомлення з топіком надіслано в канал {channel_id}, топік {topic_id}")
        else:
            # Якщо топіка немає, відправляємо без топіка
            send_message_to_channel_sync(channel_id, message)
            logger.info(f"Повідомлення без топіка надіслано в канал {channel_id}")


    logger.info(f"Всі повідомлення були надіслані.")
# def send_task_reminders():
#     """Формує список тасок і надсилає в Telegram-топіки по проєктах, згруповане по користувачам"""
#     active_statuses = ["In progress", "To Do", "Need fix", "Review"]
#     tasks = Task.objects.filter(status__in=active_statuses).order_by("project", "person", "finish")

#     if not tasks.exists():
#         return  # Немає тасок для повідомлення

#     grouped_tasks = {}

#     # Групуємо таски за проектом та користувачем
#     for task in tasks:
#         if not task.person or task.person.strip() == "Unknown Person":
#             continue  # Пропускаємо таски з невідомим виконавцем

#         project = ChanellAndTopik.objects.filter(project_external_id=task.project).first()  # Отримуємо об'єкт проєкту за `project`
#         if not project:
#             continue  # Пропускаємо таски без проєкту або без топіка

#         if project.project_external_id not in grouped_tasks:
#             grouped_tasks[project.project_external_id] = {}

#         # Якщо користувача немає в групуванні, додаємо його
#         if task.person not in grouped_tasks[project.project_external_id]:
#             grouped_tasks[project.project_external_id][task.person] = []

#         overdue = "🔴 Прострочена" if task.finish and task.finish < now().date() else "🟢 В межах графіку"

#         # Додаємо лінк у назву таски
#         task_name_with_link = f"[{task.name}]({task.task_url})" if task.task_url else task.name

#         # Додаємо таску до відповідного користувача
#         grouped_tasks[project.project_external_id][task.person].append(
#             f"📌 {task_name_with_link} (🕒 {task.hours_plan or 0} год / DDL {task.finish.strftime('%d.%m.%Y') if task.finish else '—'} / {task.status} / {overdue})"
#         )

#     # Створюємо повідомлення та надсилаємо
#     for project_external_id, users_tasks in grouped_tasks.items():
#         project = ChanellAndTopik.objects.filter(project_external_id=project_external_id).first()
#         if not project:
#             continue

#         channel_id = project.channel_id
#         topic_id = project.topik_id
#         message = f"📢 *Планові таски по проєкту на поточний тиждень:* \n______\n"

#         # Формуємо повідомлення по кожному користувачу
#         for person, task_list in users_tasks.items():
#             message += f"\n👤 @{person}\n" + "\n".join(task_list) + "\n______\n"

#         # Надсилаємо повідомлення в топік
#         send_message_to_topic_sync(channel_id, topic_id, message)


@app.task
def execute_task_reminders():
    # Виконання задач по черзі
    chain(
        execute_projects_tasks.s(),
        send_task_reminders.s(),
        
        
    )()