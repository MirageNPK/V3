# Generated by Django 5.1.3 on 2025-01-08 07:15

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('nontion_sync', '0007_notionorders_business_unit_id'),
    ]

    operations = [
        migrations.AddField(
            model_name='notionorders',
            name='record_hash',
            field=models.CharField(blank=True, max_length=64, null=True),
        ),
    ]
