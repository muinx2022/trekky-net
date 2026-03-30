from django.contrib.auth import get_user_model
from django.test import TestCase

from .models import Comment, CommentStatus, Post


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
