from django.contrib import admin

from .models import AIAutomationSettings, GA4AnalyticsSettings


@admin.register(GA4AnalyticsSettings)
class GA4AnalyticsSettingsAdmin(admin.ModelAdmin):
    list_display = ("property_id", "measurement_id", "is_connected", "updated_at")


@admin.register(AIAutomationSettings)
class AIAutomationSettingsAdmin(admin.ModelAdmin):
    list_display = ("timezone", "content_enabled", "comments_enabled", "openai_enabled", "anthropic_enabled", "updated_at")

# Register your models here.
