# Generated by Django 5.1.3 on 2025-01-31 11:19

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('nontion_sync', '0017_alter_project_status'),
    ]

    operations = [
        migrations.AlterField(
            model_name='project',
            name='status',
            field=models.CharField(choices=[('Backlog', 'Backlog'), ('In progress', 'In progress'), ('Complete', 'Complete')], max_length=50, verbose_name='Status'),
        ),
    ]
