from django.contrib.auth.tokens import default_token_generator
from django.contrib.auth import get_user_model
from django.core import mail
from django.test import TestCase
from django.test.utils import override_settings
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from rest_framework.test import APIClient

from trekky_apps.accounts.views import _resolve_frontend_url
from trekky_apps.integrations.models import EmailAuthSettings


User = get_user_model()


class UserModelTests(TestCase):
    def test_document_id_generated_for_user(self):
        user = User.objects.create_user(email="user-doc@example.com", username="userdoc", password="Secret123!")
        self.assertEqual(len(user.document_id), 24)


@override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend")
class AuthApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.email_settings = EmailAuthSettings.get_solo()
        self.email_settings.from_email = "noreply@example.com"
        self.email_settings.frontend_base_url = "http://localhost:3001"
        self.email_settings.save()

    def test_register_returns_tokens(self):
        response = self.client.post(
            "/api/v1/auth/register/",
            {"email": "newuser@example.com", "username": "newuser", "password": "TestPass123!"},
            format="json",
        )

        self.assertEqual(response.status_code, 201)
        self.assertTrue(response.data.get("access"))
        self.assertTrue(response.data.get("refresh"))
        self.assertTrue(User.objects.filter(email="newuser@example.com").exists())

    def test_forgot_password_sends_email(self):
        user = User.objects.create_user(email="forgot@example.com", username="forgotuser", password="TestPass123!")

        response = self.client.post(
            "/api/v1/auth/forgot-password/",
            {"email": user.email},
            format="json",
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn("/reset-password", mail.outbox[0].body)

    def test_reset_password_updates_credentials(self):
        user = User.objects.create_user(email="reset@example.com", username="resetuser", password="OldPass123!")
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        token = default_token_generator.make_token(user)

        response = self.client.post(
            "/api/v1/auth/reset-password/",
            {"uid": uid, "token": token, "password": "NewPass123!"},
            format="json",
        )

        self.assertEqual(response.status_code, 200)
        user.refresh_from_db()
        self.assertTrue(user.check_password("NewPass123!"))


@override_settings(MOBILE_FRONTEND_SCHEMES=["trekky"])
class GoogleOAuthMobileTests(TestCase):
    def test_mobile_frontend_scheme_is_allowed(self):
        resolved = _resolve_frontend_url("trekky://auth", "http://localhost:3001")
        self.assertEqual(resolved, "trekky://auth")

    def test_unknown_custom_scheme_falls_back_to_web_url(self):
        resolved = _resolve_frontend_url("unknown://auth", "http://localhost:3001")
        self.assertEqual(resolved, "http://localhost:3001")
