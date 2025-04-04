from django.contrib import admin
from .models import TrainingMaterial, ChatHistory, Tok, ChanellAndTopik, Feedback

@admin.register(TrainingMaterial)
class ConfigAdmin(admin.ModelAdmin):
    list_display = ["name", "telegram_user_id", "project"]
# Register your models here.
@admin.register(ChatHistory)
class ConfigAdmin(admin.ModelAdmin):
    list_display = ["user_id", "timestamp"]

@admin.register(Tok)
class ConfigAdmin(admin.ModelAdmin):
    list_display = ["name", "telegram_id"]


@admin.register(ChanellAndTopik)
class ChanellAndTopikAdmin(admin.ModelAdmin):
    list_display = ["topikandcanel_name", "channel_id", "topik_id", "project"]

# Адмінка для Feedback
@admin.register(Feedback)
class FeedbackAdmin(admin.ModelAdmin):
    list_display = ["original_response", "user_id", "corrected_response"]