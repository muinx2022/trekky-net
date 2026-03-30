import json
import os
import random
import re
from dataclasses import dataclass
from datetime import datetime
from typing import Literal
from zoneinfo import ZoneInfo

import requests
from anthropic import Anthropic
from croniter import croniter
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.db import transaction
from django.utils import timezone
from openai import OpenAI

from trekky_apps.content.media_services import DownloadedMedia, build_body_html, create_media_asset
from trekky_apps.content.models import Comment, CommentStatus, Post
from trekky_apps.engagement.models import Interaction
from trekky_apps.integrations.models import AIAutomationSettings, ImageProvider, MediaMode
from trekky_apps.taxonomy.models import Category, Tag


User = get_user_model()
JOB_NAME = Literal["content", "comments"]
LOCK_TTL_SECONDS = 15 * 60
FETCH_TIMEOUT_SECONDS = int(os.getenv("AI_AUTOMATION_FETCH_TIMEOUT_MS", "15000")) / 1000
MAX_REMOTE_IMAGE_BYTES = int(os.getenv("AI_AUTOMATION_MAX_IMAGE_BYTES", str(10 * 1024 * 1024)))
DEFAULT_SCENARIOS = "\n".join(
    [
        "An sang o mot quan via he la, khong phai quan quen",
        "Di xe do hoac xe lua duong dai",
        "Ngu homestay o tinh le, chu nha nguoi dia phuong",
        "Bat gap mot canh binh minh hoac hoang hon khong co tinh",
        "Ghe cho dia phuong buoi sang som, khong phai cho du lich",
        "An mot mon dac san vung mien lan dau",
        "Di bien trai mua hoac bien vang",
        "Leo nui hoac di trail ngan",
        "Nghi dem o khach san nho tinh le, view binh thuong nhung yen",
    ]
)
DEFAULT_CONTENT_PROMPT = (
    "Hay tao bai viet bang tieng Viet, giong nguoi that dang ke lai trai nghiem du lich doi thuong. "
    "Tra ve JSON hop le voi cac key: title, excerpt, body_text, related_tags, image_search_queries, media_mode. "
    "related_tags la mang 3-6 tag ngan. image_search_queries la mang 5-8 query tieng Anh de tim anh doi thuong, candid, real life. "
    "media_mode chi nhan body hoac gallery."
)
DEFAULT_COMMENT_PROMPT = "Hay viet 1 comment ngan, tu nhien, giong nguoi dung Viet Nam that."
DEFAULT_REPLY_PROMPT = "Hay viet 1 comment reply ngan, tu nhien, lien quan truc tiep toi comment dang duoc reply."


@dataclass
class SelectedModel:
    provider: str
    model: str
    api_key: str


@dataclass
class RemoteImageCandidate:
    provider: str
    url: str
    alt: str = ""


@dataclass(frozen=True)
class GenericContentCategory:
    document_id: str
    name: str
    slug: str


GENERIC_CONTENT_CATEGORY = GenericContentCategory(
    document_id="generic-content",
    name="Du lich va trai nghiem",
    slug="du-lich-va-trai-nghiem",
)


def get_ai_settings() -> AIAutomationSettings:
    settings = AIAutomationSettings.get_solo()
    if not settings.content_scenario_prompt:
        settings.content_scenario_prompt = DEFAULT_SCENARIOS
    if not settings.content_prompt:
        settings.content_prompt = DEFAULT_CONTENT_PROMPT
    if not settings.comment_prompt:
        settings.comment_prompt = DEFAULT_COMMENT_PROMPT
    if not settings.reply_prompt:
        settings.reply_prompt = DEFAULT_REPLY_PROMPT
    return settings


def parse_lines(value: str) -> list[str]:
    return [line.strip() for line in str(value or "").splitlines() if line.strip()]


def cron_due(expression: str, now: datetime, tz_name: str, last_run_at: datetime | None) -> bool:
    zone = ZoneInfo(tz_name or "Asia/Ho_Chi_Minh")
    zoned_now = now.astimezone(zone)
    if last_run_at and last_run_at.astimezone(zone).strftime("%Y-%m-%d %H:%M") == zoned_now.strftime("%Y-%m-%d %H:%M"):
        return False
    base = zoned_now.replace(second=0, microsecond=0)
    previous = croniter(expression, base).get_prev(datetime)
    return previous == base


def enabled_models(settings: AIAutomationSettings) -> list[SelectedModel]:
    models: list[SelectedModel] = []
    openai_key = settings.openai_api_key or os.getenv("OPENAI_API_KEY", "")
    anthropic_key = settings.anthropic_api_key or os.getenv("ANTHROPIC_API_KEY", "")
    if settings.openai_enabled and openai_key:
        for model in settings.openai_models:
            models.append(SelectedModel(provider="openai", model=str(model), api_key=openai_key))
    if settings.anthropic_enabled and anthropic_key:
        for model in settings.anthropic_models:
            models.append(SelectedModel(provider="anthropic", model=str(model), api_key=anthropic_key))
    return models


def choose_seeded_users() -> list:
    return list(User.objects.filter(is_seeded=True, is_active=True))


def choose_categories(settings: AIAutomationSettings) -> list[Category]:
    document_ids = settings.content_category_document_ids or []
    queryset = Category.objects.all()
    if document_ids:
        queryset = queryset.filter(document_id__in=document_ids)
    return list(queryset.order_by("sort_order", "name"))


def slugify_tags(raw_tags: list[str]) -> list[Tag]:
    tags: list[Tag] = []
    for name in raw_tags[:6]:
        clean_name = str(name).strip()
        if not clean_name:
            continue
        tag, _ = Tag.objects.get_or_create(name=clean_name, defaults={"slug": clean_name.lower().replace(" ", "-")})
        tags.append(tag)
    return tags


def strip_json_fence(text: str) -> str:
    cleaned = str(text or "").strip()
    cleaned = re.sub(r"^```json\s*", "", cleaned)
    cleaned = re.sub(r"^```\s*", "", cleaned)
    cleaned = re.sub(r"\s*```$", "", cleaned)
    return cleaned.strip()


def openai_text(model: str, api_key: str, prompt: str) -> str:
    client = OpenAI(api_key=api_key)
    response = client.responses.create(model=model, input=prompt)
    return (response.output_text or "").strip()


def anthropic_text(model: str, api_key: str, prompt: str) -> str:
    client = Anthropic(api_key=api_key)
    response = client.messages.create(model=model, max_tokens=1500, messages=[{"role": "user", "content": prompt}])
    return "\n".join(getattr(block, "text", "") for block in response.content if getattr(block, "text", "")).strip()


def model_text(selected: SelectedModel, prompt: str) -> str:
    if selected.provider == "openai":
        return openai_text(selected.model, selected.api_key, prompt)
    return anthropic_text(selected.model, selected.api_key, prompt)


def normalize_content_payload(payload: dict, scenario: str, preferred_media_mode: str) -> dict:
    related_tags = [str(item).strip() for item in payload.get("related_tags", []) if str(item).strip()][:6]
    image_search_queries = [str(item).strip() for item in payload.get("image_search_queries", []) if str(item).strip()][:8]
    if not image_search_queries:
        title = str(payload.get("title") or scenario).strip()
        image_search_queries = [title, scenario]
    media_mode = str(payload.get("media_mode") or preferred_media_mode or MediaMode.BODY).strip().lower()
    if media_mode not in {MediaMode.BODY, MediaMode.GALLERY}:
        media_mode = MediaMode.BODY
    return {
        "title": str(payload.get("title") or f"AI Post {timezone.now():%Y%m%d%H%M%S}").strip(),
        "excerpt": str(payload.get("excerpt") or "").strip(),
        "body_text": str(payload.get("body_text") or payload.get("content") or "").strip(),
        "related_tags": related_tags,
        "image_search_queries": image_search_queries,
        "media_mode": media_mode,
    }


def generate_content_payload(settings: AIAutomationSettings, category: Category, scenario: str) -> dict:
    pool = enabled_models(settings)
    if not pool:
        raise ValueError("No enabled AI provider/model configured for content generation")
    prompt = (
        f"{settings.content_prompt or DEFAULT_CONTENT_PROMPT}\n"
        f"Category: {category.name}\n"
        f"Scenario: {scenario}\n"
        "Return valid JSON only."
    )
    errors = []
    for selected in random.sample(pool, len(pool)):
        try:
            text = model_text(selected, prompt)
            payload = json.loads(strip_json_fence(text))
            normalized = normalize_content_payload(payload, scenario, settings.content_preferred_media_mode)
            normalized["_provider"] = selected.provider
            normalized["_model"] = selected.model
            return normalized
        except Exception as exc:
            errors.append(f"{selected.provider}:{selected.model} {exc}")
    raise ValueError(errors[-1] if errors else "Unable to generate content")


def generate_comment_text(settings: AIAutomationSettings, post: Post, reply_to: Comment | None) -> tuple[str, SelectedModel]:
    pool = enabled_models(settings)
    if not pool:
        raise ValueError("No enabled AI provider/model configured for comment generation")
    prompt = (
        f"{settings.reply_prompt if reply_to else settings.comment_prompt}\n"
        f"Post title: {post.title}\n"
        f"Post excerpt: {post.excerpt}\n"
    )
    if reply_to:
        prompt += f'Reply to comment from {reply_to.author_name}: "{reply_to.content}"\n'
    prompt += "Write only the comment text in Vietnamese, 1-2 short sentences."
    errors = []
    for selected in random.sample(pool, len(pool)):
        try:
            return model_text(selected, prompt), selected
        except Exception as exc:
            errors.append(f"{selected.provider}:{selected.model} {exc}")
    raise ValueError(errors[-1] if errors else "Unable to generate comment")


def update_job_status(settings: AIAutomationSettings, job: str, **patch):
    for key, value in patch.items():
        setattr(settings, f"{job}_{key}", value)
    settings.save(update_fields=[f"{job}_{key}" for key in patch.keys()] + ["updated_at"])


def with_job_lock(job: str, callback):
    lock_key = f"trekky:ai-automation:{job}:lock"
    if not cache.add(lock_key, timezone.now().isoformat(), LOCK_TTL_SECONDS):
        raise ValueError(f"{job} job is already running")
    try:
        return callback()
    finally:
        cache.delete(lock_key)


def resolve_image_provider(settings: AIAutomationSettings, provider: str) -> str:
    normalized = str(provider or ImageProvider.AUTO).lower()
    if normalized == ImageProvider.AUTO:
        if settings.google_image_search_enabled and settings.google_image_search_api_key and settings.google_image_search_engine_id:
            return ImageProvider.GOOGLE
        if settings.pexels_enabled and settings.pexels_api_key:
            return ImageProvider.PEXELS
    return normalized


def has_image_provider_credentials(settings: AIAutomationSettings, provider: str) -> bool:
    resolved = resolve_image_provider(settings, provider)
    if resolved == ImageProvider.GOOGLE:
        return bool(
            settings.google_image_search_enabled
            and (settings.google_image_search_api_key or os.getenv("GOOGLE_IMAGE_SEARCH_API_KEY", ""))
            and (settings.google_image_search_engine_id or os.getenv("GOOGLE_IMAGE_SEARCH_ENGINE_ID", ""))
        )
    if resolved == ImageProvider.PEXELS:
        return bool(settings.pexels_enabled and (settings.pexels_api_key or os.getenv("PEXELS_API_KEY", "")))
    return False


def search_google_images(settings: AIAutomationSettings, query: str, count: int) -> list[RemoteImageCandidate]:
    if not has_image_provider_credentials(settings, ImageProvider.GOOGLE):
        return []
    response = requests.get(
        "https://www.googleapis.com/customsearch/v1",
        params={
            "key": settings.google_image_search_api_key or os.getenv("GOOGLE_IMAGE_SEARCH_API_KEY", ""),
            "cx": settings.google_image_search_engine_id or os.getenv("GOOGLE_IMAGE_SEARCH_ENGINE_ID", ""),
            "q": query,
            "searchType": "image",
            "num": min(max(count, 1), 10),
            "safe": "active",
        },
        timeout=FETCH_TIMEOUT_SECONDS,
    )
    response.raise_for_status()
    payload = response.json()
    return [
        RemoteImageCandidate(
            provider=ImageProvider.GOOGLE,
            url=item.get("link", ""),
            alt=item.get("title") or item.get("snippet") or "",
        )
        for item in payload.get("items", [])
        if item.get("link")
    ]


def search_pexels_images(settings: AIAutomationSettings, query: str, count: int) -> list[RemoteImageCandidate]:
    if not has_image_provider_credentials(settings, ImageProvider.PEXELS):
        return []
    response = requests.get(
        "https://api.pexels.com/v1/search",
        params={
            "query": query,
            "orientation": "landscape",
            "per_page": max(count * 3, 10),
        },
        headers={"Authorization": settings.pexels_api_key or os.getenv("PEXELS_API_KEY", "")},
        timeout=FETCH_TIMEOUT_SECONDS,
    )
    response.raise_for_status()
    payload = response.json()
    return [
        RemoteImageCandidate(
            provider=ImageProvider.PEXELS,
            url=(photo.get("src") or {}).get("large2x")
            or (photo.get("src") or {}).get("large")
            or (photo.get("src") or {}).get("original")
            or "",
            alt=photo.get("alt") or "",
        )
        for photo in payload.get("photos", [])
        if (photo.get("src") or {}).get("large2x") or (photo.get("src") or {}).get("large") or (photo.get("src") or {}).get("original")
    ]


def search_remote_images(settings: AIAutomationSettings, query: str, count: int, provider: str) -> list[RemoteImageCandidate]:
    resolved = resolve_image_provider(settings, provider)
    if resolved == ImageProvider.GOOGLE:
        return search_google_images(settings, query, count)
    if resolved == ImageProvider.PEXELS:
        return search_pexels_images(settings, query, count)
    google = search_google_images(settings, query, count)
    return google if google else search_pexels_images(settings, query, count)


def download_remote_image(candidate: RemoteImageCandidate, index: int, slug_base: str) -> DownloadedMedia:
    response = requests.get(
        candidate.url,
        headers={"User-Agent": "trekky-django-ai-automation/1.0"},
        timeout=FETCH_TIMEOUT_SECONDS,
    )
    response.raise_for_status()
    content_type = str(response.headers.get("content-type", "")).lower()
    if not content_type.startswith("image/"):
        raise ValueError(f'Unsupported image content-type "{content_type}"')
    content = response.content
    if not content:
        raise ValueError("Downloaded image is empty")
    if len(content) > MAX_REMOTE_IMAGE_BYTES:
        raise ValueError("Downloaded image exceeds size limit")
    extension = (
        ".png"
        if "png" in content_type
        else ".webp"
        if "webp" in content_type
        else ".gif"
        if "gif" in content_type
        else ".jpg"
    )
    filename = f"{slug_base}-{index + 1}{extension}"
    return DownloadedMedia(
        filename=filename,
        content=content,
        mime_type=content_type,
        alt_text=candidate.alt,
        source="ai",
    )


def upload_downloaded_images(downloads: list[DownloadedMedia], author) -> list:
    uploaded = []
    for download in downloads:
        uploaded.append(
            create_media_asset(
                filename=download.filename,
                content=download.content,
                mime_type=download.mime_type,
                uploader=author,
                alt_text=download.alt_text,
                source=download.source,
            )
        )
    return uploaded


@transaction.atomic
def run_content_automation() -> dict:
    def _run():
        settings = get_ai_settings()
        now = timezone.now()
        update_job_status(settings, "content", last_run_at=now, last_error="")
        result = {
            "job": "content",
            "created_posts": 0,
            "uploaded_images": 0,
            "embedded_body_images": 0,
            "gallery_images": 0,
            "skipped": 0,
            "errors": [],
        }
        users = choose_seeded_users()
        categories = choose_categories(settings)
        if not users:
            raise ValueError("No seeded users available for AI content")
        scenarios = parse_lines(settings.content_scenario_prompt or DEFAULT_SCENARIOS)
        for _ in range(settings.content_posts_per_run):
            try:
                author = random.choice(users)
                category = random.choice(categories) if categories else GENERIC_CONTENT_CATEGORY
                scenario_pool = [item for item in scenarios if item != settings.content_last_scenario] or scenarios
                scenario = random.choice(scenario_pool)
                payload = generate_content_payload(settings, category, scenario)
                uploaded_assets = []

                if has_image_provider_credentials(settings, settings.content_image_provider):
                    desired_count = random.randint(settings.content_image_count_min, settings.content_image_count_max)
                    remote_images: list[RemoteImageCandidate] = []
                    for query in payload["image_search_queries"]:
                        try:
                            batch = search_remote_images(settings, query, desired_count, settings.content_image_provider)
                        except Exception as exc:
                            result["errors"].append(f"[content:{payload['title']}] image search: {exc}")
                            continue
                        for item in batch:
                            if not any(existing.url == item.url for existing in remote_images):
                                remote_images.append(item)
                            if len(remote_images) >= desired_count:
                                break
                        if len(remote_images) >= desired_count:
                            break

                    downloads = []
                    for index, candidate in enumerate(remote_images[:desired_count]):
                        try:
                            downloads.append(download_remote_image(candidate, index, post_slug(payload["title"])))
                        except Exception as exc:
                            result["errors"].append(f"[content:{payload['title']}] image {index + 1}: {exc}")
                    if downloads:
                        uploaded_assets = upload_downloaded_images(downloads, author)
                    elif remote_images:
                        result["errors"].append(f"[content:{payload['title']}] Unable to download remote images")
                else:
                    result["errors"].append(f"[content:{payload['title']}] Missing image provider credentials, created text-only post")

                use_body_mode = payload["media_mode"] == MediaMode.BODY and bool(uploaded_assets)
                post = Post.objects.create(
                    title=payload["title"],
                    excerpt=payload["excerpt"],
                    content=build_body_html(payload["body_text"], uploaded_assets) if use_body_mode else payload["body_text"],
                    author=author,
                    is_published=False,
                    ai_source={
                        "provider": payload.get("_provider"),
                        "model": payload.get("_model"),
                        "generated_at": timezone.now().isoformat(),
                        "scenario": scenario,
                        "image_queries": payload["image_search_queries"],
                        "media_mode": payload["media_mode"],
                    },
                )
                if isinstance(category, Category):
                    post.categories.add(category)
                post.tags.set(slugify_tags(payload["related_tags"]))
                if uploaded_assets and not use_body_mode:
                    from trekky_apps.content.media_services import attach_media_assets_to_post

                    attach_media_assets_to_post(post, [asset.id for asset in uploaded_assets])
                    result["gallery_images"] += len(uploaded_assets)
                else:
                    result["embedded_body_images"] += len(uploaded_assets)
                result["uploaded_images"] += len(uploaded_assets)
                result["created_posts"] += 1
                settings.content_last_scenario = scenario
                settings.save(update_fields=["content_last_scenario", "updated_at"])
            except Exception as exc:
                result["skipped"] += 1
                result["errors"].append(str(exc))

        update_job_status(
            settings,
            "content",
            last_success_at=timezone.now(),
            last_error=" | ".join(result["errors"])[:1000] if result["errors"] else "",
        )
        return result

    return with_job_lock("content", _run)


@transaction.atomic
def run_comment_automation() -> dict:
    def _run():
        settings = get_ai_settings()
        now = timezone.now()
        update_job_status(settings, "comments", last_run_at=now, last_error="")
        result = {"job": "comments", "created_comments": 0, "skipped": 0, "errors": []}
        users = choose_seeded_users()
        if not users:
            raise ValueError("No seeded users available for AI comments")

        posts = list(Post.objects.filter(is_published=True).select_related("author").order_by("?")[: max(settings.comments_per_run * 3, 20)])
        if not posts:
            raise ValueError("No published posts available for AI comments")

        for post in posts[: settings.comments_per_run]:
            try:
                actor_pool = [user for user in users if user.id != post.author_id] or users
                actor = random.choice(actor_pool)
                existing_comments = list(Comment.objects.filter(target_type="post", target_document_id=post.document_id).order_by("?")[:50])
                reply_target = random.choice(existing_comments) if settings.comments_allow_replies and existing_comments and random.random() < 0.5 else None
                generated, _selected = generate_comment_text(settings, post, reply_target)
                if not generated.strip():
                    result["skipped"] += 1
                    continue
                Comment.objects.create(
                    target_type="post",
                    target_document_id=post.document_id,
                    parent=reply_target,
                    author=actor,
                    author_name=actor.username or actor.email,
                    author_email=actor.email,
                    content=generated.strip(),
                    status=CommentStatus.PUBLISHED,
                )
                Interaction.objects.get_or_create(user=actor, target_type="post", target_document_id=post.document_id, action_type="like")
                if post.author_id and post.author_id != actor.id and getattr(post.author, "document_id", None):
                    Interaction.objects.get_or_create(
                        user=actor,
                        target_type="user",
                        target_document_id=post.author.document_id,
                        action_type="follow",
                    )
                result["created_comments"] += 1
            except Exception as exc:
                result["skipped"] += 1
                result["errors"].append(str(exc))

        update_job_status(
            settings,
            "comments",
            last_success_at=timezone.now(),
            last_error=" | ".join(result["errors"])[:1000] if result["errors"] else "",
        )
        return result

    return with_job_lock("comments", _run)


def post_slug(title: str) -> str:
    normalized = re.sub(r"[^a-zA-Z0-9]+", "-", str(title or "").lower()).strip("-")
    return normalized[:120] or f"ai-post-{timezone.now():%Y%m%d%H%M%S}"


def run_due_ai_automation() -> list[dict]:
    settings = get_ai_settings()
    now = timezone.now()
    results = []
    if settings.content_enabled and cron_due(settings.content_cron, now, settings.timezone, settings.content_last_run_at):
        results.append(run_content_automation())
    if settings.comments_enabled and cron_due(settings.comments_cron, now, settings.timezone, settings.comments_last_run_at):
        results.append(run_comment_automation())
    return results
