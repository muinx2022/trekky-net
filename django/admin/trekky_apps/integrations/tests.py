from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase

from trekky_apps.content.models import Comment, Post
from trekky_apps.engagement.models import Interaction
from trekky_apps.integrations.ai_automation import run_comment_automation, run_content_automation
from trekky_apps.integrations.models import AIAutomationSettings


User = get_user_model()


class AIAutomationTests(TestCase):
    def setUp(self):
        self.author = User.objects.create_user(
            email="author@example.com",
            username="author",
            password="Secret123!",
            is_seeded=True,
        )
        self.actor = User.objects.create_user(
            email="actor@example.com",
            username="actor",
            password="Secret123!",
            is_seeded=True,
        )
        self.settings = AIAutomationSettings.get_solo()

    @patch("trekky_apps.integrations.ai_automation.generate_comment_text")
    def test_comment_automation_auto_follows_post_author_by_user_document_id(self, mock_generate_comment_text):
        post = Post.objects.create(
            title="Published post",
            excerpt="Excerpt",
            content="Body",
            author=self.author,
            is_published=True,
        )
        mock_generate_comment_text.return_value = ("Comment text", None)
        self.settings.comments_per_run = 1
        self.settings.save(update_fields=["comments_per_run", "updated_at"])

        with patch("trekky_apps.integrations.ai_automation.random.choice", side_effect=[self.actor, post]):
            result = run_comment_automation()

        self.assertEqual(result["created_comments"], 1)
        self.assertTrue(
            Interaction.objects.filter(
                user=self.actor,
                target_type="user",
                target_document_id=self.author.document_id,
                action_type="follow",
            ).exists()
        )

    @patch("trekky_apps.integrations.ai_automation.generate_content_payload")
    @patch("trekky_apps.integrations.ai_automation.has_image_provider_credentials", return_value=False)
    def test_content_automation_uses_generic_category_fallback_when_none_configured(self, _mock_images, mock_generate_content_payload):
        mock_generate_content_payload.return_value = {
            "title": "Fallback category post",
            "excerpt": "Excerpt",
            "body_text": "Body text",
            "related_tags": ["fallback"],
            "image_search_queries": ["fallback travel"],
            "media_mode": "body",
            "_provider": "openai",
            "_model": "gpt-4.1-mini",
        }
        self.settings.content_posts_per_run = 1
        self.settings.content_category_document_ids = ["missing-category"]
        self.settings.save(update_fields=["content_posts_per_run", "content_category_document_ids", "updated_at"])

        result = run_content_automation()

        self.assertEqual(result["created_posts"], 1)
        post = Post.objects.get(title="Fallback category post")
        self.assertEqual(post.categories.count(), 0)
        self.assertTrue(post.author.is_seeded)
        self.assertEqual(post.ai_generated_by, "openai:gpt-4.1-mini")
        self.assertEqual(mock_generate_content_payload.call_args.args[1].document_id, "generic-content")

    @patch("trekky_apps.integrations.ai_automation.generate_content_payload")
    @patch("trekky_apps.integrations.ai_automation.has_image_provider_credentials", return_value=False)
    def test_content_automation_avoids_repeating_last_scenario_when_possible(self, _mock_images, mock_generate_content_payload):
        mock_generate_content_payload.return_value = {
            "title": "Scenario post",
            "excerpt": "Excerpt",
            "body_text": "Body text",
            "related_tags": ["travel"],
            "image_search_queries": ["phone photo local market"],
            "media_mode": "body",
            "_provider": "openai",
            "_model": "gpt-4.1-mini",
        }
        self.settings.content_posts_per_run = 1
        self.settings.content_scenario_prompt = "first scenario\nsecond scenario"
        self.settings.content_last_scenario = "first scenario"
        self.settings.save(
            update_fields=["content_posts_per_run", "content_scenario_prompt", "content_last_scenario", "updated_at"]
        )

        run_content_automation()

        self.settings.refresh_from_db()
        self.assertEqual(self.settings.content_last_scenario, "second scenario")

    @patch("trekky_apps.integrations.ai_automation.generate_comment_text")
    def test_comment_automation_prefers_recent_posts_with_fewer_comments(self, mock_generate_comment_text):
        old_post = Post.objects.create(
            title="Old post",
            excerpt="Old",
            content="Old body",
            author=self.author,
            is_published=True,
        )
        new_post = Post.objects.create(
            title="New post",
            excerpt="New",
            content="New body",
            author=self.author,
            is_published=True,
        )
        Comment.objects.create(
            target_type="post",
            target_document_id=old_post.document_id,
            author=self.actor,
            author_name="actor",
            author_email=self.actor.email,
            content="Existing old comment",
            status="published",
        )
        mock_generate_comment_text.return_value = ("Fresh comment", None)
        self.settings.comments_per_run = 1
        self.settings.save(update_fields=["comments_per_run", "updated_at"])

        run_comment_automation()

        self.assertTrue(
            Comment.objects.filter(
                target_type="post",
                target_document_id=new_post.document_id,
                content="Fresh comment",
            ).exists()
        )
        created_comment = Comment.objects.get(
            target_type="post",
            target_document_id=new_post.document_id,
            content="Fresh comment",
        )
        self.assertTrue(created_comment.author.is_seeded)
