from rest_framework import serializers

from trekky_apps.accounts.serializers import UserSerializer
from trekky_apps.taxonomy.serializers import CategorySerializer, TagSerializer

from .models import Comment, MediaAsset, Page, Post, PostAsset


class MediaAssetSerializer(serializers.ModelSerializer):
    url = serializers.SerializerMethodField()

    def get_url(self, obj):
        return obj.cloudinary_secure_url or getattr(obj.file, "url", None)

    class Meta:
        model = MediaAsset
        fields = (
            "id",
            "document_id",
            "url",
            "alt_text",
            "original_filename",
            "mime_type",
            "size_bytes",
            "width",
            "height",
            "source",
            "cloudinary_public_id",
            "cloudinary_resource_type",
            "cloudinary_asset_folder",
            "cloudinary_secure_url",
            "cloudinary_format",
            "created_at",
        )


class PostAssetSerializer(serializers.ModelSerializer):
    media_id = serializers.IntegerField(source="media_asset_id", read_only=True)
    url = serializers.SerializerMethodField()

    def get_url(self, obj):
        if obj.media_asset_id and obj.media_asset:
            return obj.media_asset.cloudinary_secure_url or getattr(obj.media_asset.file, "url", None)
        return getattr(obj.file, "url", None)

    class Meta:
        model = PostAsset
        fields = ("id", "media_id", "file", "url", "alt_text", "sort_order")


class PostSerializer(serializers.ModelSerializer):
    author = UserSerializer(read_only=True)
    categories = CategorySerializer(many=True, read_only=True)
    tags = TagSerializer(many=True, read_only=True)
    assets = PostAssetSerializer(many=True, read_only=True)

    class Meta:
        model = Post
        fields = (
            "document_id",
            "title",
            "slug",
            "excerpt",
            "content",
            "author",
            "categories",
            "tags",
            "assets",
            "is_published",
            "published_at",
            "created_at",
            "updated_at",
            "permalink",
        )


class MyPostWriteSerializer(serializers.ModelSerializer):
    category_document_ids = serializers.ListField(child=serializers.CharField(), write_only=True, required=False)
    tag_document_ids = serializers.ListField(child=serializers.CharField(), write_only=True, required=False)
    image_ids = serializers.ListField(child=serializers.IntegerField(), write_only=True, required=False)
    status = serializers.ChoiceField(choices=("draft", "published"), write_only=True, required=False)

    class Meta:
        model = Post
        fields = (
            "document_id",
            "title",
            "slug",
            "excerpt",
            "content",
            "category_document_ids",
            "tag_document_ids",
            "image_ids",
            "status",
        )
        read_only_fields = ("document_id",)


class PageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Page
        fields = (
            "document_id",
            "title",
            "slug",
            "type",
            "content",
            "is_published",
            "published_at",
            "created_at",
            "updated_at",
        )


class CommentSerializer(serializers.ModelSerializer):
    author = UserSerializer(read_only=True)
    author_name = serializers.CharField(required=False, allow_blank=True, default="")
    author_email = serializers.EmailField(required=False, allow_blank=True, default="")

    class Meta:
        model = Comment
        fields = (
            "id",
            "document_id",
            "target_type",
            "target_document_id",
            "parent",
            "author",
            "author_name",
            "author_email",
            "content",
            "status",
            "is_published",
            "created_at",
            "updated_at",
        )
