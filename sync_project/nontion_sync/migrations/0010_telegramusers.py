# Generated by Django 5.1.3 on 2025-03-03 16:49

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('nontion_sync', '0009_task_task_url'),
    ]

    operations = [
        migrations.CreateModel(
            name='TelegramUsers',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name_tg', models.CharField(max_length=255, verbose_name='Name project')),
                ('name_notion', models.CharField(blank=True, max_length=50, null=True)),
            ],
        ),
    ]
