import json
import string
import urllib.parse
import urllib.request

from django.conf import settings
from django.contrib.auth import get_user_model
from django.http import HttpResponseRedirect
from rest_framework.permissions import AllowAny
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken


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


class GoogleOAuthInitView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        cfg = _get_google_oauth_config()
        params = {
            "client_id": cfg["client_id"],
            "redirect_uri": cfg["redirect_uri"],
            "response_type": "code",
            "scope": "openid email profile",
            "access_type": "offline",
        }
        url = "https://accounts.google.com/o/oauth2/v2/auth?" + urllib.parse.urlencode(params)
        return HttpResponseRedirect(url)


class GoogleOAuthCallbackView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        cfg = _get_google_oauth_config()
        frontend_callback = f"{cfg['frontend_url']}/connect/google/callback"
        code = request.GET.get("code")
        if not code:
            return HttpResponseRedirect(f"{frontend_callback}?error=no_code")

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
            return HttpResponseRedirect(f"{frontend_callback}?error=token_exchange_failed")

        google_access_token = token_resp.get("access_token")
        if not google_access_token:
            return HttpResponseRedirect(f"{frontend_callback}?error=no_access_token")

        # Fetch user info from Google
        try:
            info_req = urllib.request.Request(
                "https://www.googleapis.com/oauth2/v2/userinfo",
                headers={"Authorization": f"Bearer {google_access_token}"},
            )
            with urllib.request.urlopen(info_req) as resp:
                userinfo = json.loads(resp.read())
        except Exception:
            return HttpResponseRedirect(f"{frontend_callback}?error=userinfo_failed")

        google_sub = userinfo.get("sub") or userinfo.get("id")
        email = userinfo.get("email")
        if not google_sub or not email:
            return HttpResponseRedirect(f"{frontend_callback}?error=missing_userinfo")

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
            {"access_token": str(refresh.access_token), "refresh_token": str(refresh)}
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
