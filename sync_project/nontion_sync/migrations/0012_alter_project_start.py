# Generated by Django 5.1.3 on 2025-01-28 13:28

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('nontion_sync', '0011_project_parent_task'),
    ]

    operations = [
        migrations.AlterField(
            model_name='project',
            name='start',
            field=models.DateField(blank=True, null=True, verbose_name='Start'),
        ),
    ]
