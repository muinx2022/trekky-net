from django.core.management.base import BaseCommand
from django.db import transaction

from trekky_apps.content.models import MediaAsset, Post
from trekky_apps.content.post_media_service import asset_urls, delete_media_asset, ensure_asset_checksum


class Command(BaseCommand):
    help = "Backfill exact media checksums and collapse duplicate media assets safely."

    def handle(self, *args, **options):
        checksum_groups: dict[str, list[MediaAsset]] = {}
        for asset in MediaAsset.objects.order_by("id"):
            checksum = ensure_asset_checksum(asset)
            if not checksum:
                continue
            checksum_groups.setdefault(checksum, []).append(asset)

        merged_groups = 0
        removed_assets = 0
        for assets in checksum_groups.values():
            if len(assets) < 2:
                continue
            merged_groups += 1
            canonical = assets[0]
            canonical_url = canonical.cloudinary_secure_url or getattr(canonical.file, "url", "")
            duplicate_urls = set()
            for duplicate in assets[1:]:
                duplicate_urls |= asset_urls(duplicate)
                duplicate.post_assets.update(
                    media_asset=canonical,
                    file=canonical.file.name,
                    alt_text=canonical.alt_text,
                )
            if duplicate_urls:
                for post in Post.objects.order_by("id"):
                    content = str(post.content or "")
                    updated = content
                    for duplicate_url in duplicate_urls:
                        if duplicate_url and canonical_url:
                            updated = updated.replace(duplicate_url, canonical_url)
                    if updated != content:
                        Post.objects.filter(pk=post.pk).update(content=updated)
            with transaction.atomic():
                for duplicate in assets[1:]:
                    delete_media_asset(duplicate)
                    removed_assets += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"Processed {len(checksum_groups)} checksum group(s), merged {merged_groups} duplicate group(s), removed {removed_assets} asset(s)."
            )
        )
