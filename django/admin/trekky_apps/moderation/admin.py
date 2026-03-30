from django.contrib import admin

from .models import ModerationAction, ModeratorCategoryAssignment


@admin.register(ModeratorCategoryAssignment)
class ModeratorCategoryAssignmentAdmin(admin.ModelAdmin):
    list_display = ("moderator", "category", "created_at")
    list_filter = ("category",)
    search_fields = ("moderator__email", "category__name")


@admin.register(ModerationAction)
class ModerationActionAdmin(admin.ModelAdmin):
    list_display = ("moderator", "target_type", "target_document_id", "action", "created_at")
    list_filter = ("target_type", "action")
    search_fields = ("moderator__email", "target_document_id")

# Register your models here.
