from django.conf import settings
from django.db import models

from trekky_apps.common.models import DocumentedModel, TimeStampedModel


class InteractionAction(models.TextChoices):
    LIKE = "like", "Like"
    SHARE = "share", "Share"
    SAVE = "save", "Save"
    FOLLOW = "follow", "Follow"


class Interaction(TimeStampedModel):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="interactions")
    target_type = models.CharField(max_length=50)
    target_document_id = models.CharField(max_length=24, db_index=True)
    action_type = models.CharField(max_length=20, choices=InteractionAction.choices)

    class Meta:
        unique_together = ("user", "target_type", "target_document_id", "action_type")


class ReportStatus(models.TextChoices):
    PENDING = "pending", "Pending"
    REVIEWED = "reviewed", "Reviewed"
    DISMISSED = "dismissed", "Dismissed"


class Report(DocumentedModel):
    reporter = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="reports",
        null=True,
        blank=True,
    )
    target_type = models.CharField(max_length=50)
    target_document_id = models.CharField(max_length=24, db_index=True)
    reason = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=ReportStatus.choices, default=ReportStatus.PENDING)
    moderator_note = models.TextField(blank=True)

    class Meta:
        ordering = ("-created_at",)

# Create your models here.
