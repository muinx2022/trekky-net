from django.contrib.auth import get_user_model
from rest_framework import serializers


User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    documentId = serializers.CharField(source="document_id", read_only=True)
    blocked = serializers.SerializerMethodField()
    confirmed = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ("id", "document_id", "documentId", "email", "username", "role", "bio", "avatar", "blocked", "confirmed", "is_seeded")

    def get_blocked(self, obj):
        return not obj.is_active

    def get_confirmed(self, obj):
        return True


class ProfileUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ("username", "bio", "avatar")

    def validate_username(self, value):
        user = self.instance
        qs = User.objects.exclude(pk=user.pk).filter(username=value)
        if qs.exists():
            raise serializers.ValidationError("Username is already in use.")
        return value
