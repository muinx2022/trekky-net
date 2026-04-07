from urllib.parse import urljoin

from django.conf import settings
from django.core.mail import EmailMultiAlternatives, get_connection
from django.template import Context, Template

from .models import EmailAuthSettings


def get_email_auth_settings() -> EmailAuthSettings:
    return EmailAuthSettings.get_solo()


def _normalize_base_url(raw_url: str | None) -> str:
    value = (raw_url or "").strip()
    if value:
        return value.rstrip("/") + "/"
    return getattr(settings, "FRONTEND_URL", "http://localhost:3001").rstrip("/") + "/"


def build_frontend_url(path: str, **query_params: str) -> str:
    email_settings = get_email_auth_settings()
    base_url = _normalize_base_url(email_settings.frontend_base_url)
    normalized_path = path if path.startswith("/") else f"/{path}"
    url = urljoin(base_url, normalized_path.lstrip("/"))
    if not query_params:
        return url
    from urllib.parse import urlencode

    separator = "&" if "?" in url else "?"
    return f"{url}{separator}{urlencode(query_params)}"


def render_email_template(template_string: str, context: dict[str, str]) -> str:
    template = Template(template_string or "")
    rendered = template.render(Context(context, autoescape=False))
    return rendered.strip()


def send_configured_email(*, subject: str, body: str, to: list[str], reply_to: list[str] | None = None) -> None:
    email_settings = get_email_auth_settings()
    connection = get_connection(
        host=email_settings.smtp_host or None,
        port=email_settings.smtp_port,
        username=email_settings.smtp_username or None,
        password=email_settings.smtp_password or None,
        use_tls=email_settings.smtp_use_tls,
        use_ssl=email_settings.smtp_use_ssl,
        timeout=email_settings.smtp_timeout or None,
        fail_silently=False,
    )
    from_email = email_settings.from_email or getattr(settings, "DEFAULT_FROM_EMAIL", "") or "no-reply@trekky.local"
    if email_settings.from_name:
        from_email = f"{email_settings.from_name} <{from_email}>"
    message = EmailMultiAlternatives(
        subject=(subject or "").replace("\n", " ").replace("\r", " ").strip(),
        body=body,
        from_email=from_email,
        to=to,
        reply_to=reply_to or ([email_settings.reply_to] if email_settings.reply_to else None),
        connection=connection,
    )
    message.send(fail_silently=False)

