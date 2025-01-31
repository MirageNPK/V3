from django.db import models
from django.core.exceptions import ValidationError
from nontion_sync.models import Project

class TrainingMaterial(models.Model):
    MATERIAL_TYPE_CHOICES = [
        ("project", "Project"),  # ТЗ для конкретного проекту
        ("general", "General"),  # Матеріал для загального використання
    ]

    name = models.CharField(max_length=255, verbose_name="Name of material or specification")
    direction = models.CharField(max_length=50, choices=MATERIAL_TYPE_CHOICES, verbose_name="Direction")
    content = models.TextField(verbose_name="Text of specification or material")
    telegram_user_id = models.CharField(max_length=50, null=True, blank=True, verbose_name="Telegram User ID who provided the material")
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name="training_materials", verbose_name="Project", null=True, blank=True)

    def __str__(self):
        return self.name

    def clean(self):
        """
        Custom validation for TrainingMaterial model.
        Ensures the following:
        - If 'direction' is 'project', 'project' field must not be null.
        - If 'direction' is 'general', 'project' field must be null.
        """
        if self.direction == "project" and not self.project:
            raise ValidationError("For materials with direction 'Project', you must select a project.")
        if self.direction == "general" and self.project:
            raise ValidationError("For materials with direction 'General', the project field must be empty.")

    def save(self, *args, **kwargs):
        # Call the clean method to validate before saving
        self.clean()
        super().save(*args, **kwargs)
