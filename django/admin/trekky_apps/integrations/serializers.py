from rest_framework import serializers

from .models import AIAutomationSettings, EmailAuthSettings, GA4AnalyticsSettings, GoogleOAuthSettings, MediaStorageSettings


class GA4AnalyticsSettingsSerializer(serializers.ModelSerializer):
    class Meta:
        model = GA4AnalyticsSettings
        fields = "__all__"


class AIAutomationSettingsSerializer(serializers.ModelSerializer):
    class Meta:
        model = AIAutomationSettings
        fields = "__all__"


class MediaStorageSettingsSerializer(serializers.ModelSerializer):
    class Meta:
        model = MediaStorageSettings
        fields = "__all__"


class GoogleOAuthSettingsSerializer(serializers.ModelSerializer):
    class Meta:
        model = GoogleOAuthSettings
        fields = "__all__"


class EmailAuthSettingsSerializer(serializers.ModelSerializer):
    class Meta:
        model = EmailAuthSettings
        fields = "__all__"
