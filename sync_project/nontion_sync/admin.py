from django.contrib import admin
from .models import NotionDbConfig, NotionOrders, Project, Parent, Task, AIgenTask, TelegramUsers

@admin.register(NotionDbConfig)
class NotionDbConfigAdmin(admin.ModelAdmin):
    list_display = ["name", "notion_token", "database_id", "is_active"]

@admin.register(NotionOrders)
class NotionOrdersAdmin(admin.ModelAdmin):
    list_display = ["name", "service_name", "service_id", "order_cost", "finish_date"]

@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ["name", "id", "direction", "start", "finish_fact", "status"]

@admin.register(Parent)
class ParentAdmin(admin.ModelAdmin):
    list_display = ["name", "project", "start", "finish", "progress"]

@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ["name", "project", "start", "finish", "person", "status"]

@admin.register(AIgenTask)
class AIgenTaskAdmin(admin.ModelAdmin):
    list_display = ["name", "project", "person", "status"]

@admin.register(TelegramUsers)
class TelegramUsersAdmin(admin.ModelAdmin):
    list_display = ["name_notion", "name_tg"]