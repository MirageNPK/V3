from django.contrib import admin
from .models import NotionDbConfig, NotionOrders, Project, Parent, Task, AIgenTask

@admin.register(NotionDbConfig)
class ConfigAdmin(admin.ModelAdmin):
    list_display = ["name", "notion_token", "database_id", "is_active"]

@admin.register(NotionOrders)
class ConfigAdmin(admin.ModelAdmin):
    list_display = ["name", "service_name", "service_id", "order_cost","finish_date"]

@admin.register(Project)
class ConfigAdmin(admin.ModelAdmin):
    list_display = ["name","id", "direction", "start", "finish_fact","status"]

@admin.register(Parent)
class ConfigAdmin(admin.ModelAdmin):
    list_display = ["name", "project", "start", "finish","progress"]

@admin.register(Task)
class ConfigAdmin(admin.ModelAdmin):
    list_display = ["name", "project", "start", "finish","person","status"]

@admin.register(AIgenTask)
class ConfigAdmin(admin.ModelAdmin):
    list_display = ["name", "project", "person","status"]