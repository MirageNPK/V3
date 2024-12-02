from django.core.management.base import BaseCommand
from sync_app.tasks import bu_projects

class Command(BaseCommand):
    help = 'Запуск автоматичного синхронізації з Notion'

    def handle(self, *args, **kwargs):
        # Запуск фонової задачі
        self.stdout.write(self.style.SUCCESS('Завдання для синхронізації з Notion запущено.'))
        bu_projects()
        

