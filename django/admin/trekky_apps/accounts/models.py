from django.contrib.auth.models import AbstractUser
from django.db import IntegrityError, models

from trekky_apps.common.models import TimeStampedModel, generate_document_id


class UserRole(models.TextChoices):
    ADMIN = "admin", "Admin"
    EDITOR = "editor", "Editor"
    MODERATOR = "moderator", "Moderator"
    USER = "user", "User"


class User(AbstractUser):
    email = models.EmailField(unique=True)
    document_id = models.CharField(max_length=24, unique=True, db_index=True, blank=True)
    role = models.CharField(max_length=32, choices=UserRole.choices, default=UserRole.USER)
    bio = models.TextField(blank=True)
    avatar = models.ImageField(upload_to="avatars/", blank=True, null=True)
    is_seeded = models.BooleanField(default=False)
    google_sub = models.CharField(max_length=255, blank=True)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["username"]

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
        raise RuntimeError("Could not generate a unique user document_id after 10 attempts")

    def __str__(self):
        return self.email


class UserSessionAudit(TimeStampedModel):
    user = models.ForeignKey("accounts.User", on_delete=models.CASCADE, related_name="session_audits")
    user_agent = models.CharField(max_length=255, blank=True)
    ip_address = models.GenericIPAddressField(blank=True, null=True)

    def __str__(self):
        return f"{self.user.email} @ {self.created_at:%Y-%m-%d %H:%M}"

# Create your models here.
