from django.conf import settings
from django.db import models
from django.utils import timezone

from trekky_apps.common.models import DocumentedModel, PublishableModel, SluggedModel


class PageType(models.TextChoices):
    HOME = "home", "Home"
    FOOTER = "footer", "Footer"


class Post(PublishableModel, SluggedModel):
    title = models.CharField(max_length=255)
    excerpt = models.TextField(blank=True)
    content = models.TextField()
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="posts",
        null=True,
        blank=True,
    )
    categories = models.ManyToManyField("taxonomy.Category", related_name="posts", blank=True)
    tags = models.ManyToManyField("taxonomy.Tag", related_name="posts", blank=True)
    ai_source = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ("-published_at", "-created_at")

    @property
    def permalink(self):
        return f"/p/{self.slug}--{self.document_id}"

    def save(self, *args, **kwargs):
        self.sync_slug(self.title)
        if self.is_published and not self.published_at:
            self.published_at = timezone.now()
        if not self.is_published and self.published_at:
            self.published_at = None
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title


class MediaAsset(DocumentedModel):
    file = models.FileField(upload_to="media-assets/")
    uploader = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="uploaded_media_assets",
        null=True,
        blank=True,
    )
    alt_text = models.CharField(max_length=255, blank=True)
    original_filename = models.CharField(max_length=255, blank=True)
    mime_type = models.CharField(max_length=100, blank=True)
    size_bytes = models.PositiveIntegerField(default=0)
    width = models.PositiveIntegerField(null=True, blank=True)
    height = models.PositiveIntegerField(null=True, blank=True)
    source = models.CharField(max_length=50, blank=True, default="upload")
    cloudinary_public_id = models.CharField(max_length=255, blank=True, db_index=True)
    cloudinary_resource_type = models.CharField(max_length=32, blank=True, default="image")
    cloudinary_asset_folder = models.CharField(max_length=255, blank=True, db_index=True)
    cloudinary_secure_url = models.URLField(blank=True)
    cloudinary_format = models.CharField(max_length=32, blank=True)

    class Meta:
        ordering = ("-created_at",)

    def __str__(self):
        return self.original_filename or self.file.name


class PostAsset(models.Model):
    post = models.ForeignKey("content.Post", on_delete=models.CASCADE, related_name="assets")
    media_asset = models.ForeignKey(
        "content.MediaAsset",
        on_delete=models.SET_NULL,
        related_name="post_assets",
        null=True,
        blank=True,
    )
    file = models.FileField(upload_to="post-assets/")
    alt_text = models.CharField(max_length=255, blank=True)
    sort_order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ("sort_order", "id")


class Page(PublishableModel, SluggedModel):
    title = models.CharField(max_length=255)
    type = models.CharField(max_length=20, choices=PageType.choices)
    content = models.TextField(blank=True)

    class Meta:
        ordering = ("title",)

    def save(self, *args, **kwargs):
        self.sync_slug(self.title)
        if self.is_published and not self.published_at:
            self.published_at = timezone.now()
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title


class CommentStatus(models.TextChoices):
    PUBLISHED = "published", "Published"
    HIDDEN = "hidden", "Hidden"
    PENDING = "pending", "Pending"
    REMOVED = "removed", "Removed"


class Comment(PublishableModel):
    target_type = models.CharField(max_length=50)
    target_document_id = models.CharField(max_length=24, db_index=True)
    parent = models.ForeignKey(
        "self",
        on_delete=models.CASCADE,
        related_name="children",
        blank=True,
        null=True,
    )
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="comments",
        null=True,
        blank=True,
    )
    author_name = models.CharField(max_length=255)
    author_email = models.EmailField(blank=True)
    content = models.TextField()
    status = models.CharField(max_length=20, choices=CommentStatus.choices, default=CommentStatus.PENDING)

    class Meta:
        ordering = ("created_at",)

    def save(self, *args, **kwargs):
        if self.parent_id:
            self.target_type = self.parent.target_type
            self.target_document_id = self.parent.target_document_id
        self.is_published = self.status == CommentStatus.PUBLISHED
        if self.is_published and not self.published_at:
            self.published_at = timezone.now()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.author_name}: {self.content[:40]}"

# Create your models here.
