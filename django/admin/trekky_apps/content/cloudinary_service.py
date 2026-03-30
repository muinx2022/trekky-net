from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from django.conf import settings
from django.core.files.base import ContentFile
from django.utils.dateparse import parse_datetime

from .models import MediaAsset
from trekky_apps.integrations.models import MediaProvider, MediaStorageSettings

try:
    import cloudinary.api
    import cloudinary.uploader
    from cloudinary.search import Search
except ImportError:  # pragma: no cover
    cloudinary = None
    Search = None


class CloudinaryServiceError(Exception):
    pass


@dataclass
class MediaQuery:
    folder: str = ""
    query: str = ""
    resource_type: str = "image"
    sort_by: str = "created_at"
    sort_dir: str = "desc"
    next_cursor: str = ""
    max_results: int = 30


def ensure_cloudinary_available() -> None:
    if cloudinary is None or Search is None:
        raise CloudinaryServiceError("Cloudinary SDK is not installed.")
    media_settings = MediaStorageSettings.objects.order_by("-updated_at").first()
    use_db_provider = bool(media_settings and media_settings.provider == MediaProvider.CLOUDINARY)
    use_env_provider = bool(getattr(settings, "USE_CLOUDINARY", False))
    if not use_db_provider and not use_env_provider:
        raise CloudinaryServiceError("Cloudinary storage is not enabled.")

    if use_db_provider:
        cloud_name = media_settings.cloudinary_cloud_name or getattr(settings, "CLOUDINARY_STORAGE", {}).get("CLOUD_NAME", "")
        api_key = media_settings.cloudinary_api_key or getattr(settings, "CLOUDINARY_STORAGE", {}).get("API_KEY", "")
        api_secret = media_settings.cloudinary_api_secret or getattr(settings, "CLOUDINARY_STORAGE", {}).get("API_SECRET", "")
        secure = media_settings.cloudinary_secure
        if not cloud_name or not api_key or not api_secret:
            raise CloudinaryServiceError("Cloudinary credentials are incomplete in Media Storage settings.")
        cloudinary.config(
            cloud_name=cloud_name,
            api_key=api_key,
            api_secret=api_secret,
            secure=secure,
        )


def _normalize_folder(value: str | None) -> str:
    return str(value or "").strip().strip("/")


def _search_expression(query: MediaQuery) -> str:
    parts: list[str] = []
    resource_type = str(query.resource_type or "image").strip().lower()
    if resource_type and resource_type != "all":
        parts.append(f"resource_type={resource_type}")
    folder = _normalize_folder(query.folder)
    if folder:
        parts.append(f'asset_folder="{folder}"')
    search_text = str(query.query or "").strip()
    if search_text:
        escaped = search_text.replace('"', '\\"')
        parts.append(
            "("
            f'filename:"{escaped}" OR public_id:"{escaped}" OR '
            f'tags:"{escaped}" OR context.alt:"{escaped}"'
            ")"
        )
    return " AND ".join(parts) if parts else "public_id:*"


def list_folder_tree() -> list[dict[str, Any]]:
    ensure_cloudinary_available()

    def build(folder_path: str = "") -> list[dict[str, Any]]:
        if folder_path:
            response = cloudinary.api.subfolders(folder_path)
            folders = response.get("folders", [])
        else:
            response = cloudinary.api.root_folders()
            folders = response.get("folders", [])

        nodes: list[dict[str, Any]] = []
        for item in folders:
            path = item.get("path") or item.get("name") or ""
            name = item.get("name") or Path(path).name or path
            nodes.append(
                {
                    "name": name,
                    "path": path,
                    "children": build(path),
                }
            )
        return nodes

    return build("")


def _storage_name_from_cloudinary(asset: dict[str, Any]) -> str:
    public_id = str(asset.get("public_id") or "").strip()
    fmt = str(asset.get("format") or "").strip()
    if fmt and not public_id.endswith(f".{fmt}"):
        return f"{public_id}.{fmt}"
    return public_id


def sync_media_asset_from_cloudinary(asset: dict[str, Any], uploader=None) -> MediaAsset:
    public_id = str(asset.get("public_id") or "").strip()
    if not public_id:
        raise CloudinaryServiceError("Cloudinary asset payload is missing public_id.")

    filename = Path(_storage_name_from_cloudinary(asset)).name or public_id
    defaults = {
        "uploader": uploader,
        "original_filename": filename,
        "mime_type": asset.get("format", ""),
        "size_bytes": int(asset.get("bytes") or 0),
        "width": asset.get("width") or None,
        "height": asset.get("height") or None,
        "source": asset.get("source") or "cloudinary",
        "cloudinary_resource_type": asset.get("resource_type") or "image",
        "cloudinary_asset_folder": _normalize_folder(asset.get("asset_folder") or asset.get("folder")),
        "cloudinary_secure_url": asset.get("secure_url") or "",
        "cloudinary_format": asset.get("format") or "",
    }
    media_asset = MediaAsset.objects.filter(cloudinary_public_id=public_id).first()
    if not media_asset:
        media_asset = MediaAsset(cloudinary_public_id=public_id, **defaults)
    else:
        for key, value in defaults.items():
            setattr(media_asset, key, value)

    storage_name = _storage_name_from_cloudinary(asset)
    if storage_name:
        media_asset.file.name = storage_name
    media_asset.save()
    created_at = parse_datetime(str(asset.get("created_at") or "")) if asset.get("created_at") else None
    if created_at and media_asset.created_at != created_at:
        MediaAsset.objects.filter(pk=media_asset.pk).update(created_at=created_at)
        media_asset.refresh_from_db()
    return media_asset


def normalize_cloudinary_asset(asset: dict[str, Any], uploader=None) -> dict[str, Any]:
    media_asset = sync_media_asset_from_cloudinary(asset, uploader=uploader)
    return {
        "id": media_asset.id,
        "document_id": media_asset.document_id,
        "public_id": media_asset.cloudinary_public_id,
        "folder": media_asset.cloudinary_asset_folder,
        "resource_type": media_asset.cloudinary_resource_type,
        "url": media_asset.cloudinary_secure_url or media_asset.file.url,
        "thumbnail_url": media_asset.cloudinary_secure_url or media_asset.file.url,
        "original_filename": media_asset.original_filename,
        "mime_type": media_asset.mime_type,
        "size_bytes": media_asset.size_bytes,
        "width": media_asset.width,
        "height": media_asset.height,
        "created_at": media_asset.created_at.isoformat() if media_asset.created_at else "",
    }


def list_assets(query: MediaQuery, uploader=None) -> dict[str, Any]:
    ensure_cloudinary_available()
    expression = _search_expression(query)
    search = (
        Search()
        .expression(expression)
        .sort_by(query.sort_by or "created_at", query.sort_dir or "desc")
        .max_results(max(1, min(100, int(query.max_results or 30))))
    )
    if query.next_cursor:
        search = search.next_cursor(query.next_cursor)
    result = search.execute()
    resources = result.get("resources", [])
    return {
        "items": [normalize_cloudinary_asset(item, uploader=uploader) for item in resources],
        "next_cursor": result.get("next_cursor") or "",
        "total_count": result.get("total_count"),
    }


def get_asset(public_id: str, uploader=None) -> dict[str, Any]:
    ensure_cloudinary_available()
    normalized = str(public_id or "").strip()
    if not normalized:
        raise CloudinaryServiceError("public_id is required.")
    result = Search().expression(f'public_id="{normalized}"').max_results(1).execute()
    resources = result.get("resources", [])
    if not resources:
        raise CloudinaryServiceError("Asset not found.")
    return normalize_cloudinary_asset(resources[0], uploader=uploader)


def upload_asset(file_obj, *, folder: str = "", uploader=None) -> dict[str, Any]:
    ensure_cloudinary_available()
    raw_bytes = file_obj.read()
    upload_options = {"folder": _normalize_folder(folder), "resource_type": "auto"}
    result = cloudinary.uploader.upload(ContentFile(raw_bytes, name=file_obj.name), **upload_options)
    if not isinstance(result, dict) or not result.get("public_id"):
        raise CloudinaryServiceError("Upload failed.")
    result.setdefault("source", "cloudinary")
    return normalize_cloudinary_asset(result, uploader=uploader)


def delete_asset(public_id: str, *, resource_type: str = "image") -> dict[str, Any]:
    ensure_cloudinary_available()
    normalized = str(public_id or "").strip()
    if not normalized:
        raise CloudinaryServiceError("public_id is required.")
    response = cloudinary.api.delete_resources([normalized], resource_type=resource_type or "image")
    MediaAsset.objects.filter(cloudinary_public_id=normalized).delete()
    deleted = response.get("deleted", {})
    return {
        "public_id": normalized,
        "status": deleted.get(normalized) or "unknown",
    }
