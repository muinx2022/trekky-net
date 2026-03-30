from django.conf import settings
from django.db import models

from trekky_apps.common.models import TimeStampedModel


class ModeratorCategoryAssignment(TimeStampedModel):
    moderator = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="category_assignments",
        limit_choices_to={"role": "moderator"},
    )
    category = models.ForeignKey(
        "taxonomy.Category",
        on_delete=models.CASCADE,
        related_name="moderator_assignments",
    )

    class Meta:
        unique_together = ("moderator", "category")

    def __str__(self):
        return f"{self.moderator.email} -> {self.category.name}"


class ModerationAction(TimeStampedModel):
    moderator = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="moderation_actions")
    target_type = models.CharField(max_length=50)
    target_document_id = models.CharField(max_length=24, db_index=True)
    action = models.CharField(max_length=50)
    note = models.TextField(blank=True)

# Create your models here.
