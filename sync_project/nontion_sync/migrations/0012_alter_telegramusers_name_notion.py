# Generated by Django 5.1.3 on 2025-03-03 16:53

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('nontion_sync', '0011_alter_telegramusers_name_notion_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='telegramusers',
            name='name_notion',
            field=models.CharField(blank=True, max_length=50, null=True, verbose_name='Name Notion'),
        ),
    ]
