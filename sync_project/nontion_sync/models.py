from django.db import models


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
    responsible = models.CharField(max_length=50, blank=True, null=True)
    service_name = models.CharField(max_length=300)
    description = models.TextField( verbose_name="Order description", blank=True, null=True)
    business_unit = models.CharField(max_length=250, default="Unknown Business Unit", blank=True, null=True)
    business_projects = models.CharField(max_length=250, default="Unknown Business Project", blank=True, null=True)
    team = models.CharField(max_length=250, default="Unknown team", blank=True, null=True)
    cost_allocation_type = models.CharField(max_length=250, blank=True, null=True)
    cost_allocation = models.CharField(max_length=250, blank=True, null=True)
    service_id = models.CharField(max_length=255)
    business_unit_id = models.IntegerField()
    order_cost = models.DecimalField(max_digits=10, decimal_places=2)
    finish_date = models.DateField()
    hours_unit = models.DecimalField(max_digits=12, decimal_places=2, verbose_name="Plan cost", null=True, blank=True)
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
    record_hash = models.CharField(max_length=64, null=True, blank=True)

    def __str__(self):
        return self.name
    
class Parent(models.Model):
    name = models.CharField(max_length=255, verbose_name="Parent name")
    start = models.DateField(verbose_name="Start")
    finish = models.DateField(verbose_name="Finish")
    hours_plan = models.FloatField(verbose_name="Hours plan")
    hours_fact = models.FloatField(verbose_name="Hours fact", null=True, blank=True)
    progress = models.FloatField(verbose_name="Progress", default=0)
    budget = models.DecimalField(max_digits=12, decimal_places=2, verbose_name="Budget")
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name="parents", verbose_name="Project")

    def __str__(self):
        return self.name
    
class Task(models.Model):
    name = models.CharField(max_length=255, verbose_name="Task Name")
    parent_task = models.ForeignKey(Parent, on_delete=models.CASCADE, related_name="tasks", verbose_name="Parent Task")
    hours_plan = models.FloatField(verbose_name="Hours plan")
    hours_fact = models.FloatField(verbose_name="Hours fact", null=True, blank=True)
    start = models.DateField(verbose_name="Start")
    finish = models.DateField(verbose_name="Finish")
    person = models.CharField(max_length=255, verbose_name="Person (Executor)")
    reviewer = models.CharField(max_length=255, verbose_name="Reviewer")
    status = models.CharField(max_length=50, choices=[("Backlog", "Backlog"), ("To Do", "To Do"),("Need fix", "Need fix"),("Review", "Review"),("In progress", "In progress"), ("Canceled", "Canceled"), ("Completed", "Completed")], verbose_name="Status")
    plan_cost = models.DecimalField(max_digits=12, decimal_places=2, verbose_name="Plan cost")
    fact_cost = models.DecimalField(max_digits=12, decimal_places=2, verbose_name="Fact cost", null=True, blank=True)
    business_unit = models.CharField(max_length=255, verbose_name="Business Unit")
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name="tasks", verbose_name="Project")

    def __str__(self):
        return self.name