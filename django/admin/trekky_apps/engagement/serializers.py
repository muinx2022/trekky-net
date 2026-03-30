from rest_framework import serializers

from .models import Interaction, Report


class InteractionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Interaction
        fields = ("id", "target_type", "target_document_id", "action_type", "created_at")


class ReportSerializer(serializers.ModelSerializer):
    class Meta:
        model = Report
        fields = (
            "document_id",
            "target_type",
            "target_document_id",
            "reason",
            "status",
            "moderator_note",
            "created_at",
            "updated_at",
        )

