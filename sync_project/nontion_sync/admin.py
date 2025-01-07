from django.contrib import admin
from .models import NotionDbConfig, NotionOrders

@admin.register(NotionDbConfig)
class ConfigAdmin(admin.ModelAdmin):
    list_display = ["name", "notion_token", "database_id_from", "database_id_to","is_active"]# Register your models here.

@admin.register(NotionOrders)
class ConfigAdmin(admin.ModelAdmin):
    list_display = ["name", "service_name", "service_id", "order_cost","finish_date"]# Register your models here.