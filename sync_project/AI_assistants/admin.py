from django.contrib import admin
from .models import TrainingMaterial, ChatHistory

@admin.register(TrainingMaterial)
class ConfigAdmin(admin.ModelAdmin):
    list_display = ["name", "telegram_user_id", "project"]
# Register your models here.
@admin.register(ChatHistory)
class ConfigAdmin(admin.ModelAdmin):
    list_display = ["user_id", "timestamp"]