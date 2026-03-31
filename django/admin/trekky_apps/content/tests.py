from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase

from .media_services import create_media_asset
from .models import Comment, CommentStatus, Post
from .post_media_service import delete_post_with_media, get_post_media_assets, sync_post_media


User = get_user_model()


class PostModelTests(TestCase):
    def test_document_id_generated_and_permalink_uses_it(self):
        user = User.objects.create_user(email="post@example.com", username="poster", password="secret123")
        post = Post.objects.create(title="Hello Trekky", content="Demo content", author=user)
        self.assertEqual(len(post.document_id), 24)
        self.assertTrue(post.permalink.endswith(post.document_id))


class CommentModelTests(TestCase):
    def test_reply_inherits_target(self):
        user = User.objects.create_user(email="comment@example.com", username="commenter", password="secret123")
        root = Comment.objects.create(
            author=user,
            author_name="Commenter",
            author_email=user.email,
            content="Root",
            target_type="post",
            target_document_id="abcdefghijklmnopqrstuvwx",
            status=CommentStatus.PUBLISHED,
        )
        reply = Comment.objects.create(
            author=user,
            author_name="Commenter",
            author_email=user.email,
            content="Reply",
            target_type="ignored",
            target_document_id="ignoredignoredignored12",
            parent=root,
            status=CommentStatus.PUBLISHED,
        )
        self.assertEqual(reply.target_type, "post")
        self.assertEqual(reply.target_document_id, root.target_document_id)


class PostMediaLifecycleTests(TestCase):
    PNG_BYTES = (
        b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01"
        b"\x08\x02\x00\x00\x00\x90wS\xde\x00\x00\x00\x0cIDAT\x08\x99c\xf8\x0f"
        b"\x00\x01\x01\x01\x00\x18\xdd\x8d\xb1\x00\x00\x00\x00IEND\xaeB`\x82"
    )

    def setUp(self):
        self.user = User.objects.create_user(email="media@example.com", username="media", password="secret123")

    def test_create_media_asset_reuses_existing_checksum(self):
        first = create_media_asset(
            filename="one.png",
            content=self.PNG_BYTES,
            mime_type="image/png",
            uploader=self.user,
        )
        second = create_media_asset(
            filename="two.png",
            content=self.PNG_BYTES,
            mime_type="image/png",
            uploader=self.user,
        )

        self.assertEqual(first.id, second.id)

    def test_sync_post_media_removes_unused_body_asset(self):
        asset = create_media_asset(
            filename="body.png",
            content=self.PNG_BYTES,
            mime_type="image/png",
            uploader=self.user,
        )
        post = Post.objects.create(
            title="Body post",
            content=f'<p><img src="{asset.file.url}" alt="Body image" /></p>',
            author=self.user,
        )
        previous_assets = get_post_media_assets(post)

        post.content = "<p>No image now</p>"
        post.save(update_fields=["content", "updated_at"])
        sync_post_media(post, previous_assets, [])

        self.assertFalse(Post.objects.filter(pk=post.pk, content__contains=asset.file.url).exists())
        self.assertFalse(type(asset).objects.filter(pk=asset.pk).exists())

    @patch("trekky_apps.content.post_media_service.delete_asset")
    def test_delete_post_with_media_keeps_shared_asset(self, mock_delete_asset):
        asset = create_media_asset(
            filename="shared.png",
            content=self.PNG_BYTES,
            mime_type="image/png",
            uploader=self.user,
        )
        asset.cloudinary_public_id = "trekky-net/shared"
        asset.cloudinary_secure_url = "https://res.cloudinary.com/demo/image/upload/v1/trekky-net/shared.png"
        asset.cloudinary_resource_type = "image"
        asset.save(update_fields=["cloudinary_public_id", "cloudinary_secure_url", "cloudinary_resource_type", "updated_at"])
        post_one = Post.objects.create(
            title="Shared one",
            content=f'<p><img src="{asset.cloudinary_secure_url}" alt="Shared image" /></p>',
            author=self.user,
        )
        post_two = Post.objects.create(
            title="Shared two",
            content=f'<p><img src="{asset.cloudinary_secure_url}" alt="Shared image" /></p>',
            author=self.user,
        )

        delete_post_with_media(post_one)

        self.assertFalse(Post.objects.filter(pk=post_one.pk).exists())
        self.assertTrue(Post.objects.filter(pk=post_two.pk).exists())
        self.assertTrue(type(asset).objects.filter(pk=asset.pk).exists())
        mock_delete_asset.assert_not_called()
