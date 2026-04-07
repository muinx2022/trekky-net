import json
import string
import urllib.parse
import urllib.request

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.tokens import default_token_generator
from django.http import HttpResponseRedirect
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken

from trekky_apps.accounts.serializers import ForgotPasswordSerializer, RegisterSerializer, ResetPasswordSerializer, UserSerializer
from trekky_apps.integrations.email_auth import build_frontend_url, get_email_auth_settings, render_email_template, send_configured_email


def _get_google_oauth_config():
    """Read Google OAuth config from DB (GoogleOAuthSettings), fall back to settings.py env vars."""
    try:
        from trekky_apps.integrations.models import GoogleOAuthSettings
        obj = GoogleOAuthSettings.get_solo()
        return {
            "client_id": obj.client_id or getattr(settings, "GOOGLE_CLIENT_ID", ""),
            "client_secret": obj.client_secret or getattr(settings, "GOOGLE_CLIENT_SECRET", ""),
            "redirect_uri": obj.redirect_uri or getattr(settings, "GOOGLE_REDIRECT_URI", "http://localhost:8000/api/v1/auth/google/callback/"),
            "frontend_url": obj.frontend_url or getattr(settings, "FRONTEND_URL", "http://localhost:3000"),
        }
    except Exception:
        return {
            "client_id": getattr(settings, "GOOGLE_CLIENT_ID", ""),
            "client_secret": getattr(settings, "GOOGLE_CLIENT_SECRET", ""),
            "redirect_uri": getattr(settings, "GOOGLE_REDIRECT_URI", "http://localhost:8000/api/v1/auth/google/callback/"),
            "frontend_url": getattr(settings, "FRONTEND_URL", "http://localhost:3000"),
        }


def _resolve_frontend_url(raw_url: str | None, fallback_url: str) -> str:
    if not raw_url:
        return fallback_url

    try:
        parsed = urllib.parse.urlparse(raw_url)
        fallback_parsed = urllib.parse.urlparse(fallback_url)
    except Exception:
        return fallback_url

    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        return fallback_url

    is_loopback = parsed.hostname in {"localhost", "127.0.0.1"}
    matches_configured_host = (
        parsed.scheme == fallback_parsed.scheme and parsed.netloc == fallback_parsed.netloc
    )

    if is_loopback or matches_configured_host:
        return f"{parsed.scheme}://{parsed.netloc}"

    return fallback_url


def _resolve_return_to(raw_path: str | None) -> str:
    if not raw_path:
        return "/"

    parsed = urllib.parse.urlparse(raw_path)
    if parsed.scheme or parsed.netloc:
        return "/"

    path = parsed.path or "/"
    if not path.startswith("/") or path.startswith("//"):
        return "/"

    query = f"?{parsed.query}" if parsed.query else ""
    fragment = f"#{parsed.fragment}" if parsed.fragment else ""
    return f"{path}{query}{fragment}"


def _encode_oauth_state(frontend_url: str, return_to: str) -> str:
    return json.dumps({"frontend_url": frontend_url, "return_to": return_to})


def _decode_oauth_state(raw_state: str | None, fallback_url: str) -> tuple[str, str]:
    if not raw_state:
        return fallback_url, "/"

    try:
        payload = json.loads(raw_state)
    except Exception:
        return _resolve_frontend_url(raw_state, fallback_url), "/"

    if not isinstance(payload, dict):
        return fallback_url, "/"

    frontend_url = _resolve_frontend_url(payload.get("frontend_url"), fallback_url)
    return_to = _resolve_return_to(payload.get("return_to"))
    return frontend_url, return_to


class GoogleOAuthInitView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        cfg = _get_google_oauth_config()
        frontend_url = _resolve_frontend_url(
            request.GET.get("frontend_url"), cfg["frontend_url"]
        )
        return_to = _resolve_return_to(request.GET.get("return_to"))
        params = {
            "client_id": cfg["client_id"],
            "redirect_uri": cfg["redirect_uri"],
            "response_type": "code",
            "scope": "openid email profile",
            "access_type": "offline",
            "state": _encode_oauth_state(frontend_url, return_to),
        }
        url = "https://accounts.google.com/o/oauth2/v2/auth?" + urllib.parse.urlencode(params)
        return HttpResponseRedirect(url)


class GoogleOAuthCallbackView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        cfg = _get_google_oauth_config()
        frontend_url, return_to = _decode_oauth_state(
            request.GET.get("state"), cfg["frontend_url"]
        )
        frontend_callback = f"{frontend_url}/connect/google/callback"
        code = request.GET.get("code")
        if not code:
            return HttpResponseRedirect(
                f"{frontend_callback}?{urllib.parse.urlencode({'error': 'no_code', 'next': return_to})}"
            )

        # Exchange authorization code for Google tokens
        token_data = urllib.parse.urlencode(
            {
                "code": code,
                "client_id": cfg["client_id"],
                "client_secret": cfg["client_secret"],
                "redirect_uri": cfg["redirect_uri"],
                "grant_type": "authorization_code",
            }
        ).encode()
        try:
            req = urllib.request.Request(
                "https://oauth2.googleapis.com/token",
                data=token_data,
                method="POST",
            )
            with urllib.request.urlopen(req) as resp:
                token_resp = json.loads(resp.read())
        except Exception:
            return HttpResponseRedirect(
                f"{frontend_callback}?{urllib.parse.urlencode({'error': 'token_exchange_failed', 'next': return_to})}"
            )

        google_access_token = token_resp.get("access_token")
        if not google_access_token:
            return HttpResponseRedirect(
                f"{frontend_callback}?{urllib.parse.urlencode({'error': 'no_access_token', 'next': return_to})}"
            )

        # Fetch user info from Google
        try:
            info_req = urllib.request.Request(
                "https://www.googleapis.com/oauth2/v2/userinfo",
                headers={"Authorization": f"Bearer {google_access_token}"},
            )
            with urllib.request.urlopen(info_req) as resp:
                userinfo = json.loads(resp.read())
        except Exception:
            return HttpResponseRedirect(
                f"{frontend_callback}?{urllib.parse.urlencode({'error': 'userinfo_failed', 'next': return_to})}"
            )

        google_sub = userinfo.get("sub") or userinfo.get("id")
        email = userinfo.get("email")
        if not google_sub or not email:
            return HttpResponseRedirect(
                f"{frontend_callback}?{urllib.parse.urlencode({'error': 'missing_userinfo', 'next': return_to})}"
            )

        # Find or create user
        UserModel = get_user_model()
        user = UserModel.objects.filter(google_sub=google_sub).first()
        if not user:
            user = UserModel.objects.filter(email=email).first()
            if user:
                user.google_sub = google_sub
                user.save(update_fields=["google_sub"])
        if not user:
            username = _generate_unique_username(email, UserModel)
            user = UserModel.objects.create_user(email=email, username=username, password=None)
            user.google_sub = google_sub
            user.save(update_fields=["google_sub"])

        # Issue Django SimpleJWT pair
        refresh = RefreshToken.for_user(user)
        qs = urllib.parse.urlencode(
            {
                "access_token": str(refresh.access_token),
                "refresh_token": str(refresh),
                "next": return_to,
            }
        )
        return HttpResponseRedirect(f"{frontend_callback}?{qs}")


def _generate_unique_username(email: str, UserModel) -> str:
    base = email.split("@")[0]
    allowed = set(string.ascii_lowercase + string.digits + "_")
    base = "".join(c if c in allowed else "_" for c in base.lower()) or "user"
    username = base
    counter = 1
    while UserModel.objects.filter(username=username).exists():
        username = f"{base}_{counter}"
        counter += 1
    return username


def _build_email_context(*, user, reset_url: str | None = None) -> dict[str, str]:
    email_settings = get_email_auth_settings()
    login_url = build_frontend_url(email_settings.login_path or "/")
    return {
        "email": user.email,
        "username": user.username or user.email,
        "site_name": "Trekky",
        "site_url": build_frontend_url("/"),
        "login_url": login_url,
        "reset_url": reset_url or "",
    }


class RegisterView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        try:
            email_settings = get_email_auth_settings()
            context = _build_email_context(user=user)
            send_configured_email(
                subject=render_email_template(email_settings.registration_email_subject, context),
                body=render_email_template(email_settings.registration_email_body, context),
                to=[user.email],
            )
        except Exception:
            pass

        refresh = RefreshToken.for_user(user)
        return Response(
            {
                "user": UserSerializer(user).data,
                "access": str(refresh.access_token),
                "refresh": str(refresh),
                "message": "Đăng ký thành công.",
            },
            status=201,
        )


class ForgotPasswordView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = ForgotPasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = get_user_model().objects.filter(email__iexact=serializer.validated_data["email"]).first()
        if user:
            uid = urlsafe_base64_encode(force_bytes(user.pk))
            token = default_token_generator.make_token(user)
            email_settings = get_email_auth_settings()
            reset_url = build_frontend_url(email_settings.password_reset_path or "/reset-password", uid=uid, token=token)
            context = _build_email_context(user=user, reset_url=reset_url)
            send_configured_email(
                subject=render_email_template(email_settings.password_reset_email_subject, context),
                body=render_email_template(email_settings.password_reset_email_body, context),
                to=[user.email],
            )

        return Response(
            {
                "message": "Nếu email tồn tại trong hệ thống, chúng tôi đã gửi hướng dẫn đặt lại mật khẩu.",
            }
        )


class ResetPasswordView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = ResetPasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data["user"]
        user.set_password(serializer.validated_data["password"])
        user.save(update_fields=["password"])
        return Response({"message": "Mật khẩu đã được cập nhật thành công."})
