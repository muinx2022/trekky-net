from django.db import models

from trekky_apps.common.models import TimeStampedModel


def default_openai_models():
    return ["gpt-4.1-mini", "gpt-4o-mini"]


def default_anthropic_models():
    return ["claude-haiku-4-5", "claude-sonnet-4-6"]


class GA4AnalyticsSettings(TimeStampedModel):
    property_id = models.CharField(max_length=255, blank=True)
    measurement_id = models.CharField(max_length=255, blank=True)
    client_id = models.CharField(max_length=255, blank=True)
    client_secret = models.CharField(max_length=255, blank=True)
    refresh_token = models.TextField(blank=True)
    is_connected = models.BooleanField(default=False)

    def __str__(self):
        return "GA4 Settings"


class MediaProvider(models.TextChoices):
    LOCAL = "local", "Local"
    CLOUDINARY = "cloudinary", "Cloudinary"
    CLOUDFLARE_R2 = "cloudflare_r2", "Cloudflare R2"


class MediaStorageSettings(TimeStampedModel):
    provider = models.CharField(max_length=32, choices=MediaProvider.choices, default=MediaProvider.CLOUDINARY)

    cloudinary_cloud_name = models.CharField(max_length=255, blank=True)
    cloudinary_api_key = models.CharField(max_length=255, blank=True)
    cloudinary_api_secret = models.CharField(max_length=255, blank=True)
    cloudinary_secure = models.BooleanField(default=True)

    r2_account_id = models.CharField(max_length=255, blank=True)
    r2_access_key_id = models.CharField(max_length=255, blank=True)
    r2_secret_access_key = models.CharField(max_length=255, blank=True)
    r2_bucket_name = models.CharField(max_length=255, blank=True)
    r2_public_base_url = models.CharField(max_length=255, blank=True)
    r2_endpoint_url = models.CharField(max_length=255, blank=True)
    r2_custom_domain = models.CharField(max_length=255, blank=True)

    def __str__(self):
        return "Media Storage Settings"


class AiProvider(models.TextChoices):
    OPENAI = "openai", "OpenAI"
    ANTHROPIC = "anthropic", "Anthropic"


class ImageProvider(models.TextChoices):
    AUTO = "auto", "Auto"
    GOOGLE = "google", "Google"
    PEXELS = "pexels", "Pexels"


class MediaMode(models.TextChoices):
    BODY = "body", "Body"
    GALLERY = "gallery", "Gallery"


class AIAutomationSettings(TimeStampedModel):
    timezone = models.CharField(max_length=64, default="Asia/Ho_Chi_Minh")

    content_enabled = models.BooleanField(default=False)
    content_cron = models.CharField(max_length=100, default="0 */6 * * *")
    content_posts_per_run = models.PositiveSmallIntegerField(default=1)
    content_category_document_ids = models.JSONField(default=list, blank=True)
    content_scenario_prompt = models.TextField(blank=True)
    content_last_scenario = models.TextField(blank=True, null=True)
    content_prompt = models.TextField(blank=True)
    content_image_provider = models.CharField(max_length=20, choices=ImageProvider.choices, default=ImageProvider.AUTO)
    content_image_count_min = models.PositiveSmallIntegerField(default=3)
    content_image_count_max = models.PositiveSmallIntegerField(default=5)
    content_preferred_media_mode = models.CharField(max_length=20, choices=MediaMode.choices, default=MediaMode.BODY)
    content_last_run_at = models.DateTimeField(blank=True, null=True)
    content_last_success_at = models.DateTimeField(blank=True, null=True)
    content_last_error = models.TextField(blank=True, null=True)

    comments_enabled = models.BooleanField(default=False)
    comments_cron = models.CharField(max_length=100, default="0 */6 * * *")
    comments_per_run = models.PositiveSmallIntegerField(default=3)
    comments_allow_replies = models.BooleanField(default=True)
    comment_prompt = models.TextField(blank=True)
    reply_prompt = models.TextField(blank=True)
    comments_last_run_at = models.DateTimeField(blank=True, null=True)
    comments_last_success_at = models.DateTimeField(blank=True, null=True)
    comments_last_error = models.TextField(blank=True, null=True)

    openai_enabled = models.BooleanField(default=True)
    openai_api_key = models.CharField(max_length=255, blank=True)
    openai_models = models.JSONField(default=default_openai_models, blank=True)

    anthropic_enabled = models.BooleanField(default=False)
    anthropic_api_key = models.CharField(max_length=255, blank=True)
    anthropic_models = models.JSONField(default=default_anthropic_models, blank=True)

    google_image_search_enabled = models.BooleanField(default=True)
    google_image_search_api_key = models.CharField(max_length=255, blank=True)
    google_image_search_engine_id = models.CharField(max_length=255, blank=True)

    pexels_enabled = models.BooleanField(default=True)
    pexels_api_key = models.CharField(max_length=255, blank=True)

    def __str__(self):
        return "AI Automation Settings"

    @classmethod
    def get_solo(cls):
        instance, _ = cls.objects.get_or_create(pk=1)
        return instance

class GoogleOAuthSettings(TimeStampedModel):
    client_id = models.CharField(max_length=255, blank=True)
    client_secret = models.CharField(max_length=255, blank=True)
    redirect_uri = models.CharField(max_length=500, blank=True, default="http://localhost:8000/api/v1/auth/google/callback/")
    frontend_url = models.CharField(max_length=500, blank=True, default="http://localhost:3000")

    def __str__(self):
        return "Google OAuth Settings"

    @classmethod
    def get_solo(cls):
        instance, _ = cls.objects.get_or_create(pk=1)
        return instance
