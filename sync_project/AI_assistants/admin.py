from django.contrib import admin
from .models import TrainingMaterial, ChatHistory, Tok, ChanellAndTopik

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
class ConfigAdmin(admin.ModelAdmin):
    list_display = ["topikandcanel_name", "channel_id", "topik_id", "project" ]
  