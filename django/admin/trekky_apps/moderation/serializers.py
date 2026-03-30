from rest_framework import serializers

from .models import ModerationAction, ModeratorCategoryAssignment


class ModeratorCategoryAssignmentSerializer(serializers.ModelSerializer):
    moderator_email = serializers.EmailField(source="moderator.email", read_only=True)
    category_name = serializers.CharField(source="category.name", read_only=True)

    class Meta:
        model = ModeratorCategoryAssignment
        fields = ("id", "moderator", "moderator_email", "category", "category_name", "created_at")


class ModerationActionSerializer(serializers.ModelSerializer):
    moderator_email = serializers.EmailField(source="moderator.email", read_only=True)

    class Meta:
        model = ModerationAction
        fields = ("id", "moderator", "moderator_email", "target_type", "target_document_id", "action", "note", "created_at")

