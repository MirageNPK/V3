from django.contrib import admin
from django.contrib import admin
from .models import NotionConfig

@admin.register(NotionConfig)
class ConfigAdmin(admin.ModelAdmin):
    list_display = ["name", "notion_token", "database_id"]