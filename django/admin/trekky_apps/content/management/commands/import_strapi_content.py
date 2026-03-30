import json
from pathlib import Path

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError

from trekky_apps.content.models import Page, Post


User = get_user_model()


class Command(BaseCommand):
    help = "Import a simplified Strapi export payload into Trekky Django models."

    def add_arguments(self, parser):
        parser.add_argument("payload", type=str, help="Path to a JSON export file.")

    def handle(self, *args, **options):
        payload_path = Path(options["payload"])
        if not payload_path.exists():
            raise CommandError(f"Payload file not found: {payload_path}")

        data = json.loads(payload_path.read_text(encoding="utf-8"))
        default_author, _ = User.objects.get_or_create(
            email="migration@trekky.local",
            defaults={"username": "migration", "role": "admin"},
        )

        for post_data in data.get("posts", []):
            Post.objects.update_or_create(
                document_id=post_data["document_id"],
                defaults={
                    "title": post_data["title"],
                    "slug": post_data.get("slug", ""),
                    "excerpt": post_data.get("excerpt", ""),
                    "content": post_data.get("content", ""),
                    "author": default_author,
                    "is_published": post_data.get("is_published", False),
                },
            )

        for page_data in data.get("pages", []):
            Page.objects.update_or_create(
                document_id=page_data["document_id"],
                defaults={
                    "title": page_data["title"],
                    "slug": page_data.get("slug", ""),
                    "type": page_data["type"],
                    "content": page_data.get("content", ""),
                    "is_published": page_data.get("is_published", False),
                },
            )

        self.stdout.write(self.style.SUCCESS("Strapi content import completed."))
