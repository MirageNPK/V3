# Generated by Django 5.1.3 on 2025-03-20 15:02

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('AI_assistants', '0003_tok'),
    ]

    operations = [
        migrations.AddField(
            model_name='tok',
            name='name',
            field=models.CharField(default=1, max_length=255),
            preserve_default=False,
        ),
    ]
