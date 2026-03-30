from django.contrib import admin

from .models import Comment, MediaAsset, Page, Post, PostAsset


class PostAssetInline(admin.TabularInline):
    model = PostAsset
    extra = 0


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ("title", "document_id", "author", "is_published", "published_at")
    list_filter = ("is_published", "categories", "tags")
    search_fields = ("title", "slug", "document_id")
    filter_horizontal = ("categories", "tags")
    inlines = [PostAssetInline]


@admin.register(Page)
class PageAdmin(admin.ModelAdmin):
    list_display = ("title", "type", "document_id", "is_published")
    list_filter = ("type", "is_published")
    search_fields = ("title", "slug", "document_id")


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ("author_name", "target_type", "target_document_id", "status", "created_at")
    list_filter = ("target_type", "status")
    search_fields = ("author_name", "author_email", "document_id", "target_document_id")


@admin.register(MediaAsset)
class MediaAssetAdmin(admin.ModelAdmin):
    list_display = ("original_filename", "document_id", "mime_type", "size_bytes", "source", "created_at")
    list_filter = ("source", "mime_type")
    search_fields = ("original_filename", "document_id", "alt_text")

# Register your models here.
