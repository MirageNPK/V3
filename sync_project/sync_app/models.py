from django.db import models

class NotionConfig(models.Model):
    name = models.CharField(max_length=255)
    notion_token = models.CharField(max_length=255)
    database_id = models.CharField(max_length=255)
    auth_endpoint = models.URLField()
    data_endpoint = models.URLField()
    api_login = models.CharField(max_length=255)
    api_password = models.CharField(max_length=255)
    
    def __str__(self):
        return f"Notion Config: {self.name[:10]}..."