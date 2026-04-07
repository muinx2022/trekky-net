from django.contrib.auth.password_validation import validate_password
from django.utils.encoding import force_str
from django.utils.http import urlsafe_base64_decode
from django.contrib.auth import get_user_model
from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from django.contrib.auth.tokens import default_token_generator


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


class RegisterSerializer(serializers.Serializer):
    email = serializers.EmailField()
    username = serializers.CharField(max_length=150)
    password = serializers.CharField(write_only=True, style={"input_type": "password"})

    def validate_email(self, value):
        normalized = value.strip().lower()
        if User.objects.filter(email__iexact=normalized).exists():
            raise serializers.ValidationError("Email đã được sử dụng.")
        return normalized

    def validate_username(self, value):
        normalized = value.strip()
        if User.objects.filter(username__iexact=normalized).exists():
            raise serializers.ValidationError("Tên người dùng đã tồn tại.")
        return normalized

    def validate_password(self, value):
        validate_password(value)
        return value

    def create(self, validated_data):
        return User.objects.create_user(
            email=validated_data["email"],
            username=validated_data["username"],
            password=validated_data["password"],
            role="user",
        )


class ForgotPasswordSerializer(serializers.Serializer):
    email = serializers.EmailField()


class ResetPasswordSerializer(serializers.Serializer):
    uid = serializers.CharField()
    token = serializers.CharField()
    password = serializers.CharField(write_only=True, style={"input_type": "password"})

    def validate_password(self, value):
        validate_password(value)
        return value

    def validate(self, attrs):
        try:
            user_id = force_str(urlsafe_base64_decode(attrs["uid"]))
            user = User.objects.get(pk=user_id)
        except Exception as exc:
            raise ValidationError({"uid": "Liên kết đặt lại mật khẩu không hợp lệ."}) from exc
        if not default_token_generator.check_token(user, attrs["token"]):
            raise ValidationError({"token": "Liên kết đặt lại mật khẩu đã hết hạn hoặc không hợp lệ."})
        attrs["user"] = user
        return attrs
