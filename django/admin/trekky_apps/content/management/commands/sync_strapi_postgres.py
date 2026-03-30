from __future__ import annotations

import mimetypes
from collections import defaultdict
from dataclasses import dataclass
from decimal import Decimal
from pathlib import Path
from urllib.parse import urlparse
from urllib.request import urlopen

import psycopg
from django.contrib.auth import get_user_model
from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from trekky_apps.content.models import Comment, MediaAsset, Page, Post, PostAsset
from trekky_apps.engagement.models import Interaction, Report
from trekky_apps.taxonomy.models import Category, CategoryStatus, Tag


User = get_user_model()


@dataclass
class StrapiConfig:
    host: str
    port: int
    dbname: str
    user: str
    password: str
    sslmode: str


class Command(BaseCommand):
    help = "Sync data directly from the old Strapi Postgres database into Trekky Django models."

    def add_arguments(self, parser):
        parser.add_argument("--host", required=True)
        parser.add_argument("--port", type=int, default=5432)
        parser.add_argument("--dbname", required=True)
        parser.add_argument("--user", required=True)
        parser.add_argument("--password", required=True)
        parser.add_argument("--sslmode", default="prefer")
        parser.add_argument("--download-media", action="store_true")
        parser.add_argument("--media-timeout", type=int, default=30)

    def handle(self, *args, **options):
        config = StrapiConfig(
            host=options["host"],
            port=options["port"],
            dbname=options["dbname"],
            user=options["user"],
            password=options["password"],
            sslmode=options["sslmode"],
        )

        try:
            with psycopg.connect(
                host=config.host,
                port=config.port,
                dbname=config.dbname,
                user=config.user,
                password=config.password,
                sslmode=config.sslmode,
                row_factory=psycopg.rows.dict_row,
            ) as conn:
                self.sync_everything(
                    conn=conn,
                    download_media=options["download_media"],
                    media_timeout=options["media_timeout"],
                )
        except psycopg.Error as exc:
            raise CommandError(f"Could not connect to Strapi Postgres: {exc}") from exc

    @transaction.atomic
    def sync_everything(self, conn, download_media: bool, media_timeout: int):
        users = self.sync_users(conn)
        categories = self.sync_categories(conn)
        tags = self.sync_tags(conn)
        posts = self.sync_posts(conn, users, categories, tags)
        self.sync_pages(conn)
        self.sync_comments(conn, users)
        self.sync_interactions(conn, users)
        self.sync_reports(conn, users)
        if download_media:
            self.sync_post_media(conn, posts, media_timeout)
        self.stdout.write(self.style.SUCCESS("Strapi Postgres sync completed successfully."))

    def fetch_all(self, conn, query: str):
        with conn.cursor() as cur:
            cur.execute(query)
            return cur.fetchall()

    def column_exists(self, conn, table_name: str, column_name: str) -> bool:
        rows = self.fetch_all(
            conn,
            f"""
            select 1
            from information_schema.columns
            where table_schema = 'public'
              and table_name = '{table_name}'
              and column_name = '{column_name}'
            limit 1
            """,
        )
        return bool(rows)

    def sync_users(self, conn):
        role_by_user_id = defaultdict(lambda: "user")
        role_column = "code" if self.column_exists(conn, "up_roles", "code") else "type"
        for row in self.fetch_all(
            conn,
            f"""
            select l.user_id, r.{role_column} as role_code
            from up_users_role_lnk l
            join up_roles r on r.id = l.role_id
            """,
        ):
            role_value = (row["role_code"] or "").strip().lower()
            role_by_user_id[row["user_id"]] = "user" if role_value in {"public", "authenticated"} else "editor"

        users = {}
        for row in self.fetch_all(
            conn,
            """
            select id, document_id, username, email, bio, blocked, confirmed, created_at, updated_at
            from up_users
            order by id
            """,
        ):
            email = (row["email"] or "").strip().lower()
            if not email:
                continue
            defaults = {
                "username": row["username"] or email.split("@")[0],
                "bio": row["bio"] or "",
                "role": role_by_user_id[row["id"]],
                "is_active": not bool(row["blocked"]),
            }
            user, created = User.objects.update_or_create(
                email=email,
                defaults={**defaults, "document_id": (row["document_id"] or "")[:24]},
            )
            if created and not user.has_usable_password():
                user.set_unusable_password()
                user.save(update_fields=["password"])
            users[row["id"]] = user

        self.stdout.write(f"Synced {len(users)} users")
        return users

    def sync_categories(self, conn):
        categories = {}
        for row in self.fetch_all(
            conn,
            """
            select id, document_id, name, slug, description, sort_order, created_at, updated_at, published_at
            from categories
            order by id
            """,
        ):
            category, _ = Category.objects.update_or_create(
                document_id=(row["document_id"] or "")[:24],
                defaults={
                    "name": row["name"] or "",
                    "slug": row["slug"] or "",
                    "description": row["description"] or "",
                    "sort_order": row["sort_order"] or 0,
                    "status": CategoryStatus.PUBLISHED if row["published_at"] else CategoryStatus.DRAFT,
                },
            )
            Category.objects.filter(pk=category.pk).update(
                created_at=row["created_at"],
                updated_at=row["updated_at"],
            )
            categories[row["id"]] = category

        for row in self.fetch_all(
            conn,
            """
            select category_id, inv_category_id
            from categories_parent_lnk
            """,
        ):
            child = categories.get(row["category_id"])
            parent = categories.get(row["inv_category_id"])
            if child:
                child.parent = parent
                child.save(update_fields=["parent"])

        self.stdout.write(f"Synced {len(categories)} categories")
        return categories

    def sync_tags(self, conn):
        tags = {}
        for row in self.fetch_all(
            conn,
            """
            select id, document_id, name, slug, description, aliases, created_at, updated_at
            from tags
            order by id
            """,
        ):
            tag, _ = Tag.objects.update_or_create(
                document_id=(row["document_id"] or "")[:24],
                defaults={
                    "name": row["name"] or "",
                    "slug": row["slug"] or "",
                    "description": row["description"] or "",
                    "aliases": row["aliases"] or [],
                },
            )
            Tag.objects.filter(pk=tag.pk).update(
                created_at=row["created_at"],
                updated_at=row["updated_at"],
            )
            tags[row["id"]] = tag

        self.stdout.write(f"Synced {len(tags)} tags")
        return tags

    def sync_posts(self, conn, users, categories, tags):
        posts = {}
        author_by_post_id = {row["post_id"]: users.get(row["user_id"]) for row in self.fetch_all(conn, "select post_id, user_id from posts_author_lnk")}
        category_ids_by_post = defaultdict(list)
        for row in self.fetch_all(conn, "select post_id, category_id from posts_categories_lnk order by post_id, category_ord nulls last, id"):
            category_ids_by_post[row["post_id"]].append(row["category_id"])
        tag_ids_by_post = defaultdict(list)
        for row in self.fetch_all(conn, "select post_id, tag_id from posts_tags_lnk order by post_id, tag_ord nulls last, id"):
            tag_ids_by_post[row["post_id"]].append(row["tag_id"])

        for row in self.fetch_all(
            conn,
            """
            select id, document_id, title, slug, excerpt, content, ai_source, created_at, updated_at, published_at
            from posts
            order by id
            """,
        ):
            post, _ = Post.objects.update_or_create(
                document_id=(row["document_id"] or "")[:24],
                defaults={
                    "title": row["title"] or "",
                    "slug": row["slug"] or "",
                    "excerpt": row["excerpt"] or "",
                    "content": row["content"] or "",
                    "author": author_by_post_id.get(row["id"]),
                    "is_published": bool(row["published_at"]),
                    "published_at": row["published_at"],
                    "ai_source": row["ai_source"] or {},
                },
            )
            Post.objects.filter(pk=post.pk).update(
                created_at=row["created_at"],
                updated_at=row["updated_at"],
                published_at=row["published_at"],
            )
            post.categories.set([categories[category_id] for category_id in category_ids_by_post[row["id"]] if category_id in categories])
            post.tags.set([tags[tag_id] for tag_id in tag_ids_by_post[row["id"]] if tag_id in tags])
            posts[row["id"]] = post

        self.stdout.write(f"Synced {len(posts)} posts")
        return posts

    def sync_pages(self, conn):
        pages = 0
        for row in self.fetch_all(
            conn,
            """
            select document_id, title, slug, type, content, created_at, updated_at, published_at
            from pages
            order by id
            """,
        ):
            page, _ = Page.objects.update_or_create(
                document_id=(row["document_id"] or "")[:24],
                defaults={
                    "title": row["title"] or "",
                    "slug": row["slug"] or "",
                    "type": row["type"] or "footer",
                    "content": row["content"] or "",
                    "is_published": bool(row["published_at"]),
                    "published_at": row["published_at"],
                },
            )
            Page.objects.filter(pk=page.pk).update(
                created_at=row["created_at"],
                updated_at=row["updated_at"],
                published_at=row["published_at"],
            )
            pages += 1

        self.stdout.write(f"Synced {pages} pages")

    def sync_comments(self, conn, users):
        comments = {}
        for row in self.fetch_all(
            conn,
            """
            select id, document_id, author_name, author_email, content, target_type, target_document_id, created_at, updated_at, published_at
            from comments
            order by id
            """,
        ):
            matched_user = next((user for user in users.values() if user.email == (row["author_email"] or "").strip().lower()), None)
            comment, _ = Comment.objects.update_or_create(
                document_id=(row["document_id"] or "")[:24],
                defaults={
                    "author": matched_user,
                    "author_name": row["author_name"] or (matched_user.username if matched_user else "Anonymous"),
                    "author_email": row["author_email"] or (matched_user.email if matched_user else ""),
                    "content": row["content"] or "",
                    "target_type": row["target_type"] or "post",
                    "target_document_id": (row["target_document_id"] or "")[:24],
                    "status": "published" if row["published_at"] else "pending",
                    "is_published": bool(row["published_at"]),
                    "published_at": row["published_at"],
                },
            )
            Comment.objects.filter(pk=comment.pk).update(
                created_at=row["created_at"],
                updated_at=row["updated_at"],
                published_at=row["published_at"],
            )
            comments[row["id"]] = comment

        for row in self.fetch_all(conn, "select comment_id, inv_comment_id from comments_parent_lnk"):
            child = comments.get(row["comment_id"])
            parent = comments.get(row["inv_comment_id"])
            if child and parent:
                Comment.objects.filter(pk=child.pk).update(parent=parent)

        self.stdout.write(f"Synced {len(comments)} comments")

    def sync_interactions(self, conn, users):
        interaction_user = {row["interaction_id"]: users.get(row["user_id"]) for row in self.fetch_all(conn, "select interaction_id, user_id from interactions_user_lnk")}
        count = 0
        for row in self.fetch_all(
            conn,
            """
            select id, action_type, target_type, target_document_id, created_at, updated_at
            from interactions
            order by id
            """,
        ):
            user = interaction_user.get(row["id"])
            if not user:
                continue
            interaction, _ = Interaction.objects.update_or_create(
                user=user,
                target_type=row["target_type"] or "",
                target_document_id=(row["target_document_id"] or "")[:24],
                action_type=row["action_type"] or "like",
            )
            Interaction.objects.filter(pk=interaction.pk).update(
                created_at=row["created_at"],
                updated_at=row["updated_at"],
            )
            count += 1

        self.stdout.write(f"Synced {count} interactions")

    def sync_reports(self, conn, users):
        reporter_by_report = {row["report_id"]: users.get(row["user_id"]) for row in self.fetch_all(conn, "select report_id, user_id from reports_reporter_lnk")}
        count = 0
        for row in self.fetch_all(
            conn,
            """
            select id, document_id, target_type, target_document_id, reason, status, created_at, updated_at
            from reports
            order by id
            """,
        ):
            report, _ = Report.objects.update_or_create(
                document_id=(row["document_id"] or "")[:24],
                defaults={
                    "reporter": reporter_by_report.get(row["id"]),
                    "target_type": row["target_type"] or "",
                    "target_document_id": (row["target_document_id"] or "")[:24],
                    "reason": row["reason"] or "",
                    "status": row["status"] or "pending",
                    "moderator_note": "",
                },
            )
            Report.objects.filter(pk=report.pk).update(
                created_at=row["created_at"],
                updated_at=row["updated_at"],
            )
            count += 1

        self.stdout.write(f"Synced {count} reports")

    def sync_post_media(self, conn, posts, media_timeout: int):
        files_by_post_id = defaultdict(list)
        file_rows = {
            row["id"]: row
            for row in self.fetch_all(
                conn,
                """
                select id, document_id, name, alternative_text, width, height, mime, size, url
                from files
                order by id
                """,
            )
        }
        for row in self.fetch_all(
            conn,
            """
            select related_id, file_id, "order"
            from files_related_mph
            where related_type = 'api::post.post' and field = 'images'
            order by related_id, "order" nulls last, id
            """,
        ):
            file_row = file_rows.get(row["file_id"])
            if file_row:
                files_by_post_id[row["related_id"]].append(file_row)

        created_assets = 0
        created_links = 0
        for old_post_id, post in posts.items():
            for sort_order, file_row in enumerate(files_by_post_id.get(old_post_id, []), start=1):
                media_asset, created = self.get_or_create_media_asset(file_row, media_timeout)
                if created:
                    created_assets += 1
                if not PostAsset.objects.filter(post=post, media_asset=media_asset).exists():
                    post_asset = PostAsset(
                        post=post,
                        media_asset=media_asset,
                        alt_text=file_row["alternative_text"] or "",
                        sort_order=sort_order,
                    )
                    try:
                        media_asset.file.open("rb")
                        try:
                            post_asset.file.save(
                                Path(media_asset.file.name).name,
                                ContentFile(media_asset.file.read()),
                                save=False,
                            )
                        finally:
                            media_asset.file.close()
                    except OSError:
                        filename, content = self.download_media_content(file_row["url"], file_row["name"], media_timeout)
                        post_asset.file.save(filename, ContentFile(content), save=False)
                    post_asset.save()
                    created_links += 1

        self.stdout.write(f"Synced {created_assets} media assets and {created_links} post asset links")

    def get_or_create_media_asset(self, file_row, media_timeout: int):
        media_asset = MediaAsset.objects.filter(document_id=(file_row["document_id"] or "")[:24]).first()
        if media_asset:
            return media_asset, False

        url = file_row["url"]
        if not url:
            raise CommandError(f"Missing URL for Strapi file {file_row['id']}")

        filename, content = self.download_media_content(url, file_row["name"], media_timeout, file_row["id"])
        media_asset = MediaAsset(
            document_id=(file_row["document_id"] or "")[:24],
            alt_text=file_row["alternative_text"] or "",
            original_filename=filename,
            mime_type=file_row["mime"] or mimetypes.guess_type(filename)[0] or "",
            size_bytes=len(content),
            width=file_row["width"],
            height=file_row["height"],
            source="strapi-import",
            cloudinary_secure_url=url if "res.cloudinary.com" in url else "",
        )
        media_asset.file.save(filename, ContentFile(content), save=False)
        media_asset.save()
        return media_asset, True

    def download_media_content(self, url: str, preferred_name: str | None, media_timeout: int, file_id: int | None = None):
        with urlopen(url, timeout=media_timeout) as response:
            content = response.read()
        filename = preferred_name or Path(urlparse(url).path).name or f"strapi-{file_id or 'file'}"
        return filename, content

    @staticmethod
    def normalize_size(value, fallback: int):
        if value is None:
            return fallback
        if isinstance(value, Decimal):
            return int(value * 1024 * 1024)
        try:
            return int(value)
        except (TypeError, ValueError):
            return fallback
