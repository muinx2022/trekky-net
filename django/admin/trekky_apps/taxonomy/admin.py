from django.contrib import admin

from .models import Category, Tag


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "document_id", "parent", "sort_order", "status")
    search_fields = ("name", "slug", "document_id")
    list_filter = ("status", "parent")
    ordering = ("sort_order", "name")


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ("name", "document_id")
    search_fields = ("name", "slug", "document_id")

# Register your models here.
