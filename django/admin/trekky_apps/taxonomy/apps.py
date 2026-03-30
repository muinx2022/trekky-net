from django.apps import AppConfig


class TaxonomyConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "trekky_apps.taxonomy"
    label = "taxonomy"

    def ready(self):
        import trekky_apps.taxonomy.signals  # noqa: F401
