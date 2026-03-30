import re

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from trekky_apps.accounts.seed_users import DEFAULT_SEED_PASSWORD, build_seed_user_draft
from trekky_apps.content.models import Comment, CommentStatus, Page, PageType, Post
from trekky_apps.engagement.models import Interaction, InteractionAction, Report, ReportStatus
from trekky_apps.integrations.models import AIAutomationSettings, GA4AnalyticsSettings
from trekky_apps.moderation.models import ModerationAction, ModeratorCategoryAssignment
from trekky_apps.taxonomy.models import Category, Tag


User = get_user_model()


class Command(BaseCommand):
    help = "Seed Trekky demo data for local development."

    @transaction.atomic
    def handle(self, *args, **options):
        users = self.seed_users()
        categories = self.seed_categories()
        tags = self.seed_tags()
        posts = self.seed_posts(users, categories, tags)
        self.seed_pages()
        comments = self.seed_comments(users, posts)
        self.seed_reports(users, posts, comments)
        self.seed_interactions(users, posts, comments)
        self.seed_moderation(users, categories, posts, comments)
        self.seed_integrations()
        self.stdout.write(self.style.SUCCESS("Trekky demo data seeded successfully."))

    def upsert_user(self, email, username, role, password, **extra_fields):
        user, created = User.objects.get_or_create(
            email=email,
            defaults={"username": username, "role": role, **extra_fields},
        )
        changed = False
        if user.username != username:
            user.username = username
            changed = True
        if user.role != role:
            user.role = role
            changed = True
        for key, value in extra_fields.items():
            if getattr(user, key) != value:
                setattr(user, key, value)
                changed = True
        if created or not user.check_password(password):
            user.set_password(password)
            changed = True
        if created or changed:
            user.save()
        return user

    def seed_users(self):
        users = {
            "admin": self.upsert_user(
                email="admin@trekky.local",
                username="trekkyadmin",
                role="admin",
                password="Admin123!",
                is_staff=True,
                is_superuser=True,
                first_name="Trekky",
                last_name="Admin",
            ),
            "editor": self.upsert_user(
                email="editor@trekky.local",
                username="trekkyeditor",
                role="editor",
                password="Editor123!",
                first_name="Content",
                last_name="Editor",
                is_seeded=True,
            ),
            "moderator": self.upsert_user(
                email="moderator@trekky.local",
                username="trekkymod",
                role="moderator",
                password="Moderator123!",
                first_name="Category",
                last_name="Moderator",
                is_seeded=True,
            ),
            "user": self.upsert_user(
                email="user@trekky.local",
                username="trekkyuser",
                role="user",
                password="User123!",
                first_name="Public",
                last_name="User",
                is_seeded=True,
            ),
        }
        generated_users = self.seed_generated_users(8)
        if generated_users:
            users["seed_pool"] = generated_users
        return users

    def seed_generated_users(self, count):
        existing_suffixes = set()
        for user in User.objects.filter(is_seeded=True).only("username"):
            match = re.search(r"(\d+)$", user.username or "")
            if match:
                existing_suffixes.add(int(match.group(1)))

        next_index = (max(existing_suffixes) + 1) if existing_suffixes else 1
        created_users = []
        while len(created_users) < count:
            draft = build_seed_user_draft(next_index)
            next_index += 1
            if User.objects.filter(email=draft["email"]).exists() or User.objects.filter(username=draft["username"]).exists():
                continue
            created_users.append(
                self.upsert_user(
                    email=draft["email"],
                    username=draft["username"],
                    role="user",
                    password=DEFAULT_SEED_PASSWORD,
                    first_name=draft["display_name"],
                    is_seeded=True,
                    bio=f'Seed user: {draft["display_name"]}',
                )
            )
        return created_users

    def seed_categories(self):
        travel, _ = Category.objects.update_or_create(
            document_id="cattravelguide0000000001",
            defaults={
                "name": "Travel Guides",
                "slug": "travel-guides",
                "description": "Guides and travel stories.",
                "sort_order": 1,
                "parent": None,
            },
        )
        hotels, _ = Category.objects.update_or_create(
            document_id="cathotelsreview000000001",
            defaults={
                "name": "Hotels",
                "slug": "hotels",
                "description": "Hotels and stays.",
                "sort_order": 2,
                "parent": travel,
            },
        )
        food, _ = Category.objects.update_or_create(
            document_id="catfoodreview00000000001",
            defaults={
                "name": "Food",
                "slug": "food",
                "description": "Food and cafe experiences.",
                "sort_order": 3,
                "parent": None,
            },
        )
        return {"travel": travel, "hotels": hotels, "food": food}

    def seed_tags(self):
        weekend, _ = Tag.objects.update_or_create(
            document_id="tagweekendtrip0000000001",
            defaults={"name": "Weekend Trip", "slug": "weekend-trip", "aliases": ["short trip"]},
        )
        budget, _ = Tag.objects.update_or_create(
            document_id="tagbudgettravel000000001",
            defaults={"name": "Budget Travel", "slug": "budget-travel", "aliases": ["cheap travel"]},
        )
        return {"weekend": weekend, "budget": budget}

    def seed_posts(self, users, categories, tags):
        post_1, _ = Post.objects.update_or_create(
            document_id="ukwvibz7o75zvcr1i8dvgwpq",
            defaults={
                "title": "Ngu mot em o khach san nho, view khong gi dac biet ma van thay vui",
                "slug": "ngu-mot-em-o-khach-san-nho-view-khong-gi-ac-biet-ma-van-thay-vui",
                "excerpt": "A sample migrated post with a preserved document_id.",
                "content": "This sample post preserves the public permalink format from the old Trekky site.",
                "author": users["editor"],
                "is_published": True,
                "published_at": timezone.now(),
            },
        )
        post_1.categories.set([categories["travel"], categories["hotels"]])
        post_1.tags.set([tags["weekend"], tags["budget"]])

        post_2, _ = Post.objects.update_or_create(
            document_id="demopostfood000000000001",
            defaults={
                "title": "An sang o Da Lat trong mot quan nho ben doc",
                "slug": "an-sang-o-da-lat-trong-mot-quan-nho-ben-doc",
                "excerpt": "A second seeded post for moderation and reports.",
                "content": "A seeded article for admin-app dashboards, reports, and moderation flows.",
                "author": users["user"],
                "is_published": True,
                "published_at": timezone.now(),
            },
        )
        post_2.categories.set([categories["food"]])
        post_2.tags.set([tags["budget"]])

        return {"post_1": post_1, "post_2": post_2}

    def seed_pages(self):
        Page.objects.update_or_create(
            document_id="pagehome0000000000000001",
            defaults={
                "title": "Homepage Blocks",
                "slug": "homepage-blocks",
                "type": PageType.HOME,
                "content": "Seeded homepage CMS content.",
                "is_published": True,
                "published_at": timezone.now(),
            },
        )
        Page.objects.update_or_create(
            document_id="pagefooter00000000000001",
            defaults={
                "title": "Footer Links",
                "slug": "footer-links",
                "type": PageType.FOOTER,
                "content": "Seeded footer CMS content.",
                "is_published": True,
                "published_at": timezone.now(),
            },
        )

    def seed_comments(self, users, posts):
        root, _ = Comment.objects.update_or_create(
            document_id="cmtroot00000000000000001",
            defaults={
                "target_type": "post",
                "target_document_id": posts["post_1"].document_id,
                "parent": None,
                "author": users["user"],
                "author_name": "Public User",
                "author_email": users["user"].email,
                "content": "Bai viet nay doc xong thay muon di ngay.",
                "status": CommentStatus.PUBLISHED,
                "is_published": True,
                "published_at": timezone.now(),
            },
        )
        reply, _ = Comment.objects.update_or_create(
            document_id="cmtreply0000000000000001",
            defaults={
                "target_type": "post",
                "target_document_id": posts["post_1"].document_id,
                "parent": root,
                "author": users["editor"],
                "author_name": "Content Editor",
                "author_email": users["editor"].email,
                "content": "Cam on ban, hy vong se co them nhieu review nhu vay.",
                "status": CommentStatus.PUBLISHED,
                "is_published": True,
                "published_at": timezone.now(),
            },
        )
        pending, _ = Comment.objects.update_or_create(
            document_id="cmtpending00000000000001",
            defaults={
                "target_type": "post",
                "target_document_id": posts["post_2"].document_id,
                "parent": None,
                "author": users["user"],
                "author_name": "Public User",
                "author_email": users["user"].email,
                "content": "Comment pending for moderator review.",
                "status": CommentStatus.PENDING,
                "is_published": False,
            },
        )
        return {"root": root, "reply": reply, "pending": pending}

    def seed_reports(self, users, posts, comments):
        Report.objects.update_or_create(
            document_id="rptpost00000000000000001",
            defaults={
                "reporter": users["user"],
                "target_type": "post",
                "target_document_id": posts["post_2"].document_id,
                "reason": "Potentially misleading review content.",
                "status": ReportStatus.PENDING,
            },
        )
        Report.objects.update_or_create(
            document_id="rptcmt000000000000000001",
            defaults={
                "reporter": users["editor"],
                "target_type": "comment",
                "target_document_id": comments["pending"].document_id,
                "reason": "Needs moderator review.",
                "status": ReportStatus.REVIEWED,
                "moderator_note": "Seen by editorial team.",
            },
        )

    def seed_interactions(self, users, posts, comments):
        Interaction.objects.get_or_create(
            user=users["user"],
            target_type="post",
            target_document_id=posts["post_1"].document_id,
            action_type=InteractionAction.LIKE,
        )
        Interaction.objects.get_or_create(
            user=users["moderator"],
            target_type="comment",
            target_document_id=comments["root"].document_id,
            action_type=InteractionAction.SAVE,
        )

    def seed_moderation(self, users, categories, posts, comments):
        ModeratorCategoryAssignment.objects.get_or_create(
            moderator=users["moderator"],
            category=categories["hotels"],
        )
        ModerationAction.objects.get_or_create(
            moderator=users["moderator"],
            target_type="comment",
            target_document_id=comments["pending"].document_id,
            action="review",
            defaults={"note": "Seed moderation event for dashboard testing."},
        )
        ModerationAction.objects.get_or_create(
            moderator=users["moderator"],
            target_type="post",
            target_document_id=posts["post_2"].document_id,
            action="watch",
            defaults={"note": "Seed watchlist item for category moderator."},
        )

    def seed_integrations(self):
        GA4AnalyticsSettings.objects.update_or_create(
            property_id="properties/demo-trekky",
            defaults={
                "measurement_id": "G-TREKKYDEMO",
                "client_id": "demo-ga4-client",
                "client_secret": "demo-ga4-secret",
                "refresh_token": "demo-refresh-token",
                "is_connected": True,
            },
        )
        AIAutomationSettings.objects.update_or_create(
            pk=1,
            defaults={
                "timezone": "Asia/Ho_Chi_Minh",
                "content_enabled": False,
                "content_cron": "0 */6 * * *",
                "content_posts_per_run": 1,
                "content_category_document_ids": ["cattravelguide0000000001", "cathotelsreview000000001"],
                "content_scenario_prompt": "An sang o quan nho\nNgu khach san nho view binh thuong ma vui\nDi xe lua duong dai",
                "content_last_scenario": None,
                "content_prompt": "Generate concise travel content in Vietnamese and return JSON.",
                "content_image_provider": "auto",
                "content_image_count_min": 3,
                "content_image_count_max": 5,
                "content_preferred_media_mode": "body",
                "comments_enabled": False,
                "comments_cron": "0 */6 * * *",
                "comments_per_run": 3,
                "comments_allow_replies": True,
                "comment_prompt": "Generate helpful moderation-safe comments.",
                "reply_prompt": "Generate a natural short reply in Vietnamese.",
                "openai_enabled": True,
                "openai_api_key": "",
                "openai_models": ["gpt-4.1-mini", "gpt-4o-mini"],
                "anthropic_enabled": False,
                "anthropic_api_key": "",
                "anthropic_models": ["claude-haiku-4-5"],
                "google_image_search_enabled": False,
                "google_image_search_api_key": "",
                "google_image_search_engine_id": "",
                "pexels_enabled": False,
                "pexels_api_key": "",
            },
        )
