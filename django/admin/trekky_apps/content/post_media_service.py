from __future__ import annotations

import hashlib
import re
from html.parser import HTMLParser
from typing import Iterable
from urllib.parse import urlsplit, urlunsplit

from django.db import transaction

from .cloudinary_service import CloudinaryServiceError, delete_asset
from .models import MediaAsset, Post


class PostMediaSyncError(Exception):
    pass


def normalize_media_url(value: str) -> str:
    raw = str(value or "").strip()
    if not raw:
        return ""
    parts = urlsplit(raw)
    return urlunsplit((parts.scheme, parts.netloc, parts.path, "", ""))


class _ImageSrcParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.sources: list[str] = []

    def handle_starttag(self, tag, attrs):
        if tag.lower() != "img":
            return
        for key, value in attrs:
            if key.lower() == "src" and value:
                self.sources.append(value)
                return


def extract_image_sources(content: str) -> list[str]:
    parser = _ImageSrcParser()
    parser.feed(str(content or ""))
    return [normalize_media_url(item) for item in parser.sources if normalize_media_url(item)]


def asset_urls(asset: MediaAsset) -> set[str]:
    values = {
        normalize_media_url(asset.cloudinary_secure_url),
        normalize_media_url(getattr(asset.file, "url", "")),
    }
    return {item for item in values if item}


def extract_media_assets_from_content(content: str) -> list[MediaAsset]:
    sources = set(extract_image_sources(content))
    if not sources:
        return []
    matches: list[MediaAsset] = []
    seen_ids: set[int] = set()
    for asset in MediaAsset.objects.order_by("id"):
        if asset.id in seen_ids:
            continue
        if asset_urls(asset) & sources:
            matches.append(asset)
            seen_ids.add(asset.id)
    return matches


def get_post_media_assets(post: Post) -> set[MediaAsset]:
    assets_by_id: dict[int, MediaAsset] = {}
    for post_asset in post.assets.select_related("media_asset").all():
        if post_asset.media_asset_id and post_asset.media_asset:
            assets_by_id[post_asset.media_asset_id] = post_asset.media_asset
    for asset in extract_media_assets_from_content(post.content):
        assets_by_id[asset.id] = asset
    return set(assets_by_id.values())


def compute_checksum_from_bytes(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def ensure_asset_checksum(asset: MediaAsset) -> str:
    if asset.content_checksum:
        return asset.content_checksum
    if not asset.file:
        return ""
    with asset.file.open("rb") as handle:
        checksum = compute_checksum_from_bytes(handle.read())
    MediaAsset.objects.filter(pk=asset.pk).update(content_checksum=checksum)
    asset.content_checksum = checksum
    return checksum


def asset_used_by_other_posts(asset: MediaAsset, *, excluding_post_ids: Iterable[int] = ()) -> bool:
    excluded = {int(item) for item in excluding_post_ids if item}
    if asset.post_assets.exclude(post_id__in=excluded).exists():
        return True
    candidate_posts = Post.objects.exclude(id__in=excluded).only("id", "content")
    urls = asset_urls(asset)
    if asset.cloudinary_public_id:
        pattern = re.escape(asset.cloudinary_public_id)
        for post in candidate_posts.iterator():
            if re.search(pattern, str(post.content or "")):
                return True
    for post in candidate_posts.iterator():
        if urls & set(extract_image_sources(post.content)):
            return True
    return False


def _delete_local_file(asset: MediaAsset) -> None:
    name = str(getattr(asset.file, "name", "") or "").strip()
    storage = getattr(asset.file, "storage", None)
    if name and storage and storage.exists(name):
        storage.delete(name)


def delete_media_asset(asset: MediaAsset) -> None:
    if asset.cloudinary_public_id:
        try:
            delete_asset(asset.cloudinary_public_id, resource_type=asset.cloudinary_resource_type or "image")
        except CloudinaryServiceError as exc:
            raise PostMediaSyncError(str(exc)) from exc
        return
    _delete_local_file(asset)
    asset.delete()


def delete_media_asset_if_unused(asset: MediaAsset, *, excluding_post_ids: Iterable[int] = ()) -> bool:
    if asset_used_by_other_posts(asset, excluding_post_ids=excluding_post_ids):
        return False
    delete_media_asset(asset)
    return True


@transaction.atomic
def sync_post_media(post: Post, previous_assets: set[MediaAsset], gallery_asset_ids: list[int]) -> set[MediaAsset]:
    from .media_services import attach_media_assets_to_post

    attach_media_assets_to_post(post, gallery_asset_ids)
    current_assets = get_post_media_assets(post)
    removed_assets = [asset for asset in previous_assets if asset.id not in {item.id for item in current_assets}]
    for asset in removed_assets:
        delete_media_asset_if_unused(asset, excluding_post_ids=[post.id])
    return current_assets


@transaction.atomic
def delete_post_with_media(post: Post) -> None:
    media_assets = list(get_post_media_assets(post))
    for asset in media_assets:
        delete_media_asset_if_unused(asset, excluding_post_ids=[post.id])
    post.delete()
