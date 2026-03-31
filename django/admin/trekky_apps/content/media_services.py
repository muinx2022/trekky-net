import os
import tempfile
from dataclasses import dataclass
from io import BytesIO
from pathlib import Path
import re

from django.core.files.base import ContentFile
from django.utils.html import escape
from PIL import Image, UnidentifiedImageError

from .models import MediaAsset, Post, PostAsset
from .post_media_service import compute_checksum_from_bytes
from trekky_apps.integrations.models import MediaProvider, MediaStorageSettings


MAX_IMAGE_SIZE_BYTES = int(os.getenv("AI_AUTOMATION_MAX_IMAGE_BYTES", str(10 * 1024 * 1024)))


@dataclass
class DownloadedMedia:
    filename: str
    content: bytes
    mime_type: str
    alt_text: str = ""
    source: str = "upload"


def _image_dimensions(content: bytes) -> tuple[int | None, int | None]:
    try:
        with Image.open(BytesIO(content)) as image:
            return image.width, image.height
    except (UnidentifiedImageError, OSError):
        return None, None


def create_media_asset(
    *,
    filename: str,
    content: bytes,
    mime_type: str,
    uploader=None,
    alt_text: str = "",
    source: str = "upload",
) -> MediaAsset:
    if not content:
        raise ValueError("Media content is empty")
    if len(content) > MAX_IMAGE_SIZE_BYTES and mime_type.startswith("image/"):
        raise ValueError("Media exceeds the configured size limit")
    checksum = compute_checksum_from_bytes(content)
    existing = MediaAsset.objects.filter(content_checksum=checksum).first()
    if existing:
        if alt_text and not existing.alt_text:
            existing.alt_text = alt_text
        if source and existing.source != source:
            existing.source = source
        existing.save(update_fields=["alt_text", "source", "updated_at"])
        return existing

    media_settings = MediaStorageSettings.objects.order_by("-updated_at").first()
    if media_settings and media_settings.provider == MediaProvider.CLOUDINARY:
        from .cloudinary_service import upload_asset

        payload = upload_asset(ContentFile(content, name=Path(filename).name), folder="trekky-net", uploader=uploader)
        asset = MediaAsset.objects.get(pk=payload["id"])
        asset.alt_text = alt_text or asset.alt_text
        asset.source = source or asset.source
        asset.content_checksum = checksum
        asset.save(update_fields=["alt_text", "source", "content_checksum", "updated_at"])
        return asset

    width, height = _image_dimensions(content) if mime_type.startswith("image/") else (None, None)
    asset = MediaAsset(
        uploader=uploader,
        alt_text=alt_text or "",
        original_filename=Path(filename).name,
        mime_type=mime_type or "",
        size_bytes=len(content),
        width=width,
        height=height,
        source=source,
        content_checksum=checksum,
    )
    field = asset._meta.get_field("file")
    generated_name = field.generate_filename(asset, Path(filename).name)
    saved_name = asset.file.storage.save(generated_name, ContentFile(content))
    asset.file.name = saved_name
    asset.save()
    return asset


def create_media_asset_from_upload(uploaded_file, uploader=None, *, alt_text: str = "", source: str = "upload") -> MediaAsset:
    filename = getattr(uploaded_file, "name", None) or next(tempfile._get_candidate_names())
    mime_type = getattr(uploaded_file, "content_type", "") or "application/octet-stream"
    return create_media_asset(
        filename=filename,
        content=uploaded_file.read(),
        mime_type=mime_type,
        uploader=uploader,
        alt_text=alt_text,
        source=source,
    )


def attach_media_assets_to_post(post: Post, asset_ids: list[int]) -> list[PostAsset]:
    existing = list(post.assets.order_by("sort_order", "id"))
    existing_by_asset_id = {item.media_asset_id: item for item in existing if item.media_asset_id}
    keep_ids: list[int] = []
    ordered_assets = list(MediaAsset.objects.filter(id__in=asset_ids).order_by("id"))
    asset_map = {asset.id: asset for asset in ordered_assets}
    created_or_updated: list[PostAsset] = []

    for index, asset_id in enumerate(asset_ids):
        asset = asset_map.get(asset_id)
        if not asset:
            continue
        keep_ids.append(asset.id)
        post_asset = existing_by_asset_id.get(asset.id)
        if not post_asset:
            post_asset = PostAsset(post=post, media_asset=asset)
        post_asset.file.name = asset.file.name
        post_asset.alt_text = asset.alt_text
        post_asset.sort_order = index
        post_asset.save()
        created_or_updated.append(post_asset)

    post.assets.exclude(media_asset_id__in=keep_ids).delete()
    return created_or_updated


def build_body_html(body_text: str, assets: list[MediaAsset]) -> str:
    raw = str(body_text or "").strip()
    paragraphs = [item.strip() for item in re.split(r"(?:\r?\n){2,}", raw) if item.strip()]
    if not paragraphs and raw:
        paragraphs = [raw]
    intro = "".join(f"<p>{escape(item)}</p>" for item in paragraphs)
    gallery = "".join(
        f'<p><img src="{escape(asset.cloudinary_secure_url or asset.file.url)}" alt="{escape(asset.alt_text or asset.original_filename or "Post image")}" /></p>'
        for asset in assets
    )
    return f"{intro}{gallery}"
