from django.db import models

from trekky_apps.common.models import DocumentedModel, SluggedModel


class CategoryStatus(models.TextChoices):
    DRAFT = "draft", "Draft"
    PUBLISHED = "published", "Published"


class Category(DocumentedModel, SluggedModel):
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    sort_order = models.PositiveIntegerField(default=0)
    status = models.CharField(max_length=20, choices=CategoryStatus.choices, default=CategoryStatus.DRAFT)
    parent = models.ForeignKey(
        "self",
        on_delete=models.CASCADE,
        related_name="children",
        blank=True,
        null=True,
    )

    class Meta:
        ordering = ("sort_order", "name")
        verbose_name_plural = "categories"

    def save(self, *args, **kwargs):
        self.sync_slug(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class Tag(DocumentedModel, SluggedModel):
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    aliases = models.JSONField(default=list, blank=True)

    class Meta:
        ordering = ("name",)

    def save(self, *args, **kwargs):
        self.sync_slug(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name

# Create your models here.
