import secrets
import string

from django.db import IntegrityError, models
from slugify import slugify as vendor_slugify


DOCUMENT_ID_ALPHABET = string.ascii_lowercase + string.digits


def generate_document_id(length=24):
    return "".join(secrets.choice(DOCUMENT_ID_ALPHABET) for _ in range(length))


def trekky_slugify(value: str) -> str:
    normalized = str(value or "").strip()
    if not normalized:
        return ""
    normalized = normalized.replace("đ", "d").replace("Đ", "D")
    return vendor_slugify(normalized, lowercase=True, separator="-", max_length=255)


class TimeStampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class DocumentedModel(TimeStampedModel):
    document_id = models.CharField(max_length=24, unique=True, db_index=True, blank=True)

    class Meta:
        abstract = True

    def ensure_document_id(self):
        if not self.document_id:
            self.document_id = generate_document_id()

    def save(self, *args, **kwargs):
        for _ in range(10):
            self.ensure_document_id()
            try:
                return super().save(*args, **kwargs)
            except IntegrityError:
                self.document_id = ""
        raise RuntimeError("Could not generate a unique document_id after 10 attempts")


class PublishableModel(DocumentedModel):
    is_published = models.BooleanField(default=False)
    published_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        abstract = True


class SluggedModel(models.Model):
    slug = models.SlugField(max_length=255)

    class Meta:
        abstract = True

    def sync_slug(self, value):
        if value:
            self.slug = trekky_slugify(value)

# Create your models here.
