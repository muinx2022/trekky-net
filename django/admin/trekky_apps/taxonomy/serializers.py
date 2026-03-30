from rest_framework import serializers

from .models import Category, Tag


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ("id", "document_id", "name", "slug", "description", "sort_order", "status", "parent")


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ("document_id", "name", "slug", "description", "aliases")
