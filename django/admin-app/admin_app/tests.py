from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from trekky_apps.content.media_services import create_media_asset
from trekky_apps.content.models import Comment, CommentStatus, Post, PostAsset
from trekky_apps.engagement.models import Report, ReportStatus
from trekky_apps.moderation.models import ModerationAction


User = get_user_model()


class ReportModerationFlowTests(TestCase):
    def setUp(self):
        self.admin_user = User.objects.create_user(
            email="admin@example.com",
            username="admin",
            password="Secret123!",
            role="admin",
        )
        self.reporter = User.objects.create_user(
            email="reporter@example.com",
            username="reporter",
            password="Secret123!",
        )
        self.client.force_login(self.admin_user)

    def create_post(self, **kwargs):
        defaults = {
            "title": "Flagged post",
            "excerpt": "excerpt",
            "content": "body",
            "author": self.reporter,
            "is_published": True,
        }
        defaults.update(kwargs)
        return Post.objects.create(**defaults)

    def create_report(self, **kwargs):
        defaults = {
            "reporter": self.reporter,
            "target_type": "post",
            "target_document_id": self.post.document_id,
            "reason": "Spam",
            "status": ReportStatus.PENDING,
        }
        defaults.update(kwargs)
        return Report.objects.create(**defaults)

    def test_approve_report_unpublishes_post_and_resolves_all_pending_for_target(self):
        self.post = self.create_post()
        report = self.create_report(reason="Spam")
        sibling = self.create_report(reason="Scam")
        dismissed = self.create_report(reason="Old", status=ReportStatus.DISMISSED)

        response = self.client.post(reverse("admin_app:report-approve", args=[report.document_id]), follow=True)

        self.assertRedirects(response, reverse("admin_app:report-list"))
        self.post.refresh_from_db()
        report.refresh_from_db()
        sibling.refresh_from_db()
        dismissed.refresh_from_db()

        self.assertFalse(self.post.is_published)
        self.assertIsNone(self.post.published_at)
        self.assertEqual(report.status, ReportStatus.REVIEWED)
        self.assertEqual(sibling.status, ReportStatus.REVIEWED)
        self.assertEqual(dismissed.status, ReportStatus.DISMISSED)

        action = ModerationAction.objects.get()
        self.assertEqual(action.moderator, self.admin_user)
        self.assertEqual(action.target_type, "post")
        self.assertEqual(action.target_document_id, self.post.document_id)
        self.assertEqual(action.action, "approve_post_report")
        self.assertContains(response, "Approved 2 report(s) and hid the post.")

    def test_reject_report_dismisses_group_and_leaves_post_unchanged(self):
        self.post = self.create_post()
        report = self.create_report(reason="Noise")
        sibling = self.create_report(reason="Duplicate")

        response = self.client.post(reverse("admin_app:report-reject", args=[report.document_id]), follow=True)

        self.assertRedirects(response, reverse("admin_app:report-list"))
        self.post.refresh_from_db()
        report.refresh_from_db()
        sibling.refresh_from_db()

        self.assertTrue(self.post.is_published)
        self.assertEqual(report.status, ReportStatus.DISMISSED)
        self.assertEqual(sibling.status, ReportStatus.DISMISSED)

        action = ModerationAction.objects.get()
        self.assertEqual(action.action, "reject_post_report")
        self.assertContains(response, "Rejected 2 report(s). The post was unchanged.")

    def test_approve_report_for_missing_post_still_resolves_reports(self):
        self.post = self.create_post()
        report = self.create_report()
        target_document_id = self.post.document_id
        self.post.delete()

        response = self.client.post(reverse("admin_app:report-approve", args=[report.document_id]), follow=True)

        self.assertRedirects(response, reverse("admin_app:report-list"))
        report.refresh_from_db()
        self.assertEqual(report.status, ReportStatus.REVIEWED)

        action = ModerationAction.objects.get()
        self.assertEqual(action.action, "approve_post_report")
        self.assertEqual(action.target_document_id, target_document_id)
        self.assertContains(response, "Approved 1 report(s); target post no longer exists.")

    def test_report_list_shows_target_state_and_moderation_actions(self):
        self.post = self.create_post(is_published=False)
        pending = self.create_report(reason="Needs review")
        Report.objects.create(
            reporter=self.reporter,
            target_type="post",
            target_document_id=self.post.document_id,
            reason="Handled",
            status=ReportStatus.REVIEWED,
        )

        response = self.client.get(reverse("admin_app:report-list"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Hidden")
        self.assertContains(response, "Approve")
        self.assertContains(response, "Reject")
        self.assertContains(response, reverse("admin_app:report-approve", args=[pending.document_id]))
        self.assertContains(response, reverse("admin_app:report-reject", args=[pending.document_id]))

    def test_approve_comment_report_hides_comment(self):
        self.post = self.create_post()
        comment = Comment.objects.create(
            target_type="post",
            target_document_id=self.post.document_id,
            author=self.reporter,
            author_name="Reporter",
            author_email="reporter@example.com",
            content="Flagged comment",
            status=CommentStatus.PUBLISHED,
        )
        report = Report.objects.create(
            reporter=self.reporter,
            target_type="comment",
            target_document_id=comment.document_id,
            reason="Offensive",
        )

        response = self.client.post(reverse("admin_app:report-approve", args=[report.document_id]), follow=True)

        self.assertRedirects(response, reverse("admin_app:report-list"))
        comment.refresh_from_db()
        report.refresh_from_db()
        self.assertEqual(comment.status, CommentStatus.HIDDEN)
        self.assertFalse(comment.is_published)
        self.assertEqual(report.status, ReportStatus.REVIEWED)
        self.assertContains(response, "Approved 1 report(s) and hid the comment.")


class PostDeleteFlowTests(TestCase):
    PNG_BYTES = (
        b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01"
        b"\x08\x02\x00\x00\x00\x90wS\xde\x00\x00\x00\x0cIDAT\x08\x99c\xf8\x0f"
        b"\x00\x01\x01\x01\x00\x18\xdd\x8d\xb1\x00\x00\x00\x00IEND\xaeB`\x82"
    )

    def setUp(self):
        self.admin_user = User.objects.create_user(
            email="admin-delete@example.com",
            username="admin-delete",
            password="Secret123!",
            role="admin",
        )
        self.client.force_login(self.admin_user)

    def test_admin_post_delete_removes_exclusive_media(self):
        asset = create_media_asset(
            filename="exclusive.png",
            content=self.PNG_BYTES,
            mime_type="image/png",
            uploader=self.admin_user,
        )
        post = Post.objects.create(
            title="Delete me",
            content=f'<p><img src="{asset.file.url}" alt="Exclusive image" /></p>',
            author=self.admin_user,
        )
        PostAsset.objects.create(post=post, media_asset=asset, file=asset.file.name, alt_text=asset.alt_text)

        response = self.client.post(reverse("admin_app:post-delete", args=[post.document_id]), follow=True)

        self.assertRedirects(response, reverse("admin_app:post-list"))
        self.assertFalse(Post.objects.filter(pk=post.pk).exists())
        self.assertFalse(type(asset).objects.filter(pk=asset.pk).exists())
