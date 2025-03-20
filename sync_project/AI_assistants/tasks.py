import logging
from django.utils.timezone import now
from sync_project.celery import app
from nontion_sync.models import Task, Project
from AI_assistants.bot_utils import send_message_to_topic_sync

logger = logging.getLogger(__name__)

@app.task
def send_task_reminders():
    """Формує список тасок і надсилає в Telegram-топіки по проєктах"""
    active_statuses = ["In progress", "To Do", "Need fix", "Review"]
    tasks = Task.objects.filter(status__in=active_statuses).order_by("project", "person", "finish")

    if not tasks.exists():
        return  # Немає тасок для повідомлення

    grouped_tasks = {}

    for task in tasks:
        if not task.person or task.person.strip() == "Unknown Person":
            continue  # Пропускаємо таски з невідомим виконавцем

        project = Project.objects.filter(project_id=task.project).first()  # Отримуємо об'єкт проєкту за `project`
        if not project or project.telegram_topik_id == 0:
            continue  # Пропускаємо таски без проєкту або без топіка

        if project.project_id not in grouped_tasks:
            grouped_tasks[project.project_id] = {"topic_id": project.telegram_topik_id, "tasks": {}}

        if task.person not in grouped_tasks[project.project_id]["tasks"]:
            grouped_tasks[project.project_id]["tasks"][task.person] = []

        overdue = "🔴 Прострочена" if task.finish and task.finish < now().date() else "🟢 В межах графіку"

        # Додаємо лінк у назву таски
        task_name_with_link = f"[{task.name}]({task.task_url})" if task.task_url else task.name

        grouped_tasks[project.project_id]["tasks"][task.person].append(
            f"📌 {task_name_with_link} (🕒 {task.hours_plan or 0} год / DDL {task.finish.strftime('%d.%m.%Y') if task.finish else '—'} / {task.status} / {overdue})"
        )

    for project_id, data in grouped_tasks.items():
        topic_id = data["topic_id"]
        message = f"📢 *Планові таски по проєкту на поточний тиждень:* \n______\n"

        for person, task_list in data["tasks"].items():
            message += f"\n👤 @{person}\n" + "\n".join(task_list) + "\n______\n"

        send_message_to_topic_sync(topic_id, message)
