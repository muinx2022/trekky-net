from django.apps import AppConfig


class ContentConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "trekky_apps.content"
    label = "content"

    def ready(self):
        import trekky_apps.content.signals  # noqa: F401
