from django.db import models


class NotionDbConfig(models.Model):
    name = models.CharField(max_length=255)
    notion_token = models.CharField(max_length=255)
    database_id = models.CharField(max_length=255)
    is_active = models.BooleanField(default=True)
    
    def __str__(self):
        return f"Notion Config: {self.name[:10]}..."


class NotionOrders(models.Model):
    name = models.CharField(max_length=255)
    order_id = models.CharField(max_length=50)
    responsible = models.CharField(max_length=50, blank=True, null=True)
    service_name = models.CharField(max_length=300)
    business_unit = models.CharField(max_length=250)
    service_id = models.CharField(max_length=255)
    business_unit_id = models.IntegerField()
    order_cost = models.DecimalField(max_digits=10, decimal_places=2)
    finish_date = models.DateField()
    record_hash = models.CharField(max_length=64, null=True, blank=True)

    def __str__(self):
        return f"NotionOrders: {self.name[:20]} - {self.finish_date.strftime('%d/%m/%Y')}"
