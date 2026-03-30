from django.contrib import admin

from .models import Interaction, Report


@admin.register(Interaction)
class InteractionAdmin(admin.ModelAdmin):
    list_display = ("user", "action_type", "target_type", "target_document_id", "created_at")
    list_filter = ("action_type", "target_type")
    search_fields = ("user__email", "target_document_id")


@admin.register(Report)
class ReportAdmin(admin.ModelAdmin):
    list_display = ("document_id", "target_type", "target_document_id", "status", "created_at")
    list_filter = ("status", "target_type")
    search_fields = ("document_id", "target_document_id", "reporter__email")

# Register your models here.
