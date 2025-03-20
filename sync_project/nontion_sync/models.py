from django.db import models
import uuid

class NotionDbConfig(models.Model):
    name = models.CharField(max_length=255)
    notion_token = models.CharField(max_length=255)
    database_id = models.CharField(max_length=255)
    is_active = models.BooleanField(default=True)
    
    def __str__(self):
        return f"Notion Config: {self.name[:10]}..."


class NotionOrders(models.Model):
    name = models.CharField(max_length=255)
    order_id = models.CharField(max_length=50)
    order_id_num = models.IntegerField(blank=True, null=True)
    responsible = models.CharField(max_length=50, blank=True, null=True)
    responsible_pf = models.CharField(max_length=50, choices=[("Sense", "Олександр Sense Штефан"), ("Insomnia", "Юлия Insomnia Кандалинцева"), ("Ernesto", "Olena Ernesto Ivashyna"), ("Stamford", "Vadym Stamford Didenko"), ("Vert", "Сергей Vert Брагаренко"), ("Lunna", "Анна Lunna Яковуник"), ("Degtaria", "Yana Degtaria Dehtiarova"), ("Voice", "Александр Voice Стадник"), ("Seraphina", "Oksana Seraphina Hrytsakova"), ("Pulse", "Andrii Pulse Bobanych"), ("Mirage", "Petro Mirage Pryimak"), ("SATTVA", "Інна Sattva Лисенко"), ("Demchik", "Victoria Demchik Demydova")],null=True, blank=True, verbose_name="Responsible PF")
    service_name = models.CharField(max_length=300)
    description = models.TextField( verbose_name="Order description", blank=True, null=True)
    business_unit = models.CharField(max_length=250, default="Unknown Business Unit", blank=True, null=True)
    business_projects = models.CharField(max_length=250, default="Unknown Business Project", blank=True, null=True)
    business_project_pf = models.CharField(max_length=250, default="Unknown Business Project PF", blank=True, null=True)
    category = models.CharField(max_length=250, default="Unknown Category", blank=True, null=True)
    url_docs = models.URLField(verbose_name="URL for dox",blank=True, null=True)
    team = models.CharField(max_length=250, default="Unknown team", blank=True, null=True)
    cost_allocation_type = models.CharField(max_length=250, blank=True, null=True)
    cost_allocation = models.CharField(max_length=250, blank=True, null=True)
    service_id = models.CharField(max_length=255)
    business_unit_id = models.IntegerField()
    order_cost = models.DecimalField(max_digits=10, decimal_places=2)
    finish_date = models.DateField(blank=True, null=True)
    order_date = models.DateField(blank=True, null=True)
    hours_unit = models.DecimalField(max_digits=12, decimal_places=2, verbose_name="Plan hours or unit", null=True, blank=True)
    status = models.CharField(max_length=50, choices=[("New", "New"), ("In progress", "In progress"), ("Done", "Done")],null=True, blank=True, verbose_name="Status")
    record_hash = models.CharField(max_length=64, null=True, blank=True)

    def __str__(self):
        return f"NotionOrders: {self.name[:20]} - {self.finish_date.strftime('%d/%m/%Y')}"

class Project(models.Model):
    name = models.CharField(max_length=255, verbose_name="Name project")
    project_id = models.CharField(max_length=50,null=True, blank=True)
    direction = models.CharField(max_length=255, verbose_name="Project direction")
    progress = models.FloatField(verbose_name="Progress", null=True, blank=True)
    status = models.CharField(max_length=50, choices=[("Backlog", "Backlog"), ("In progress", "In progress"), ("Complete", "Complete")], verbose_name="Status")
    start = models.DateField(verbose_name="Start", null=True, blank=True)
    finish_fact = models.DateField(verbose_name="Finish Fact", null=True, blank=True)
    plan_cost = models.DecimalField(max_digits=12, decimal_places=2, verbose_name="Plan cost", null=True, blank=True)
    fact_cost = models.DecimalField(max_digits=12, decimal_places=2, verbose_name="Fact cost", null=True, blank=True)
    project_manager = models.CharField(max_length=255, verbose_name="Project manager")
    telegram_topik_id = models.PositiveIntegerField(verbose_name="ID Підгрупи телеграму", default=0)
    record_hash = models.CharField(max_length=64, null=True, blank=True)

    def __str__(self):
        return self.name
    
class Parent(models.Model):
    name = models.CharField(max_length=255, verbose_name="Parent name")
    start = models.DateField(verbose_name="Start", null=True, blank=True)
    finish = models.DateField(verbose_name="Finish", null=True, blank=True)
    hours_plan = models.FloatField(verbose_name="Hours plan", null=True, blank=True)
    hours_fact = models.FloatField(verbose_name="Hours fact", null=True, blank=True)
    progress = models.FloatField(verbose_name="Progress", default=0, null=True, blank=True)
    budget = models.DecimalField(max_digits=12, decimal_places=2, verbose_name="Budget", null=True, blank=True)
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name="parents", verbose_name="Project")

    def __str__(self):
        return self.name
    
class Task(models.Model):
    name = models.CharField(max_length=255, verbose_name="Task Name")
    task_url = models.URLField(verbose_name="URL for task",blank=True, null=True)
    task_id = models.CharField(max_length=150,null=True, blank=True)
    parent_task = models.ForeignKey(Parent, on_delete=models.CASCADE, related_name="subtasks", verbose_name="Parent Task", null=True, blank=True)
    hours_plan = models.FloatField(verbose_name="Hours plan", null=True, blank=True)
    hours_fact = models.FloatField(verbose_name="Hours fact", null=True, blank=True)
    start = models.DateField(verbose_name="Start", null=True, blank=True)
    finish = models.DateField(verbose_name="Finish", null=True, blank=True)
    person = models.CharField(max_length=255, verbose_name="Person (Executor)", null=True, blank=True)
    person_tg = models.CharField(max_length=150, choices=[("External persons", "External persons"), ("Stamford", "dv_vadym"),("Pulse", "andrii_pulse_netpeak"),("Degtaria", "degtaria"),("Voice", "voice_netpeak"), ("Insomnia", "Julia_kandalintseva"), ("Mirage", "Petro_Pryimsk"), ("Unknown Person", "Unknown Person")], verbose_name="Person_tg", null=True, blank=True)
    status = models.CharField(max_length=50, choices=[("Backlog", "Backlog"), ("To Do", "To Do"),("Need fix", "Need fix"),("Review", "Review"),("In progress", "In progress"), ("Canceled", "Canceled"), ("Completed", "Completed")], verbose_name="Status", null=True, blank=True)
    plan_cost = models.DecimalField(max_digits=12, decimal_places=2, verbose_name="Plan cost", null=True, blank=True)
    fact_cost = models.DecimalField(max_digits=12, decimal_places=2, verbose_name="Fact cost", null=True, blank=True)
    business_unit = models.CharField(max_length=255, verbose_name="Business Unit", null=True, blank=True)
    project = models.CharField(max_length=50,null=True, blank=True)
    record_hash = models.CharField(max_length=64, null=True, blank=True)

    def __str__(self):
        return self.name
    
class AIgenTask(models.Model):
    name = models.CharField(max_length=255, verbose_name="Task Name")
    task_id = models.CharField(max_length=150,null=True, blank=True)
    parent_task = models.ForeignKey(Parent, on_delete=models.CASCADE, related_name="ai_generated_subtasks", verbose_name="Parent Task", null=True, blank=True)
    hours_plan = models.FloatField(verbose_name="Hours plan", null=True, blank=True)
    person = models.CharField(max_length=255, verbose_name="Person (Executor)", null=True, blank=True)
    status = models.CharField(max_length=50, default="Backlog", verbose_name="Status", null=True, blank=True)
    plan_cost = models.DecimalField(max_digits=12, decimal_places=2, verbose_name="Plan cost", null=True, blank=True)
    project = models.ForeignKey("Project", on_delete=models.CASCADE, verbose_name="Проєкт")
    order = models.PositiveIntegerField(verbose_name="Порядковий номер", default=0)
    record_hash = models.CharField(max_length=64, null=True, blank=True)

    def __str__(self):
        return self.name

class TelegramUsers(models.Model):
    name_tg = models.CharField(max_length=255, verbose_name="Name TG")
    name_notion = models.CharField(verbose_name="Name Notion", max_length=150,null=True, blank=True)
    

    def __str__(self):
        return self.name_notion