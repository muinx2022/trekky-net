import io
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase
from PIL import Image
from rest_framework.test import APIClient

from trekky_apps.content.models import MediaAsset, Post


User = get_user_model()


class CompatibilityApiTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email="test@example.com",
            username="tester",
            password="Secret123!",
            role="user",
        )
        self.admin = User.objects.create_user(
            email="admin-test@example.com",
            username="admin-tester",
            password="Secret123!",
            role="admin",
        )
        self.client = APIClient()
        self.client.force_authenticate(self.user)

    def test_me_endpoints_return_profile(self):
        response = self.client.get("/api/v1/me/")
        legacy_response = self.client.get("/api/v1/users/me")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(legacy_response.status_code, 200)
        self.assertEqual(response.json()["email"], "test@example.com")
        self.assertEqual(response.json()["document_id"], self.user.document_id)
        self.assertEqual(response.json()["documentId"], self.user.document_id)
        self.assertEqual(legacy_response.json()["email"], "test@example.com")
        self.assertEqual(legacy_response.json()["documentId"], self.user.document_id)

    def test_upload_and_legacy_post_flow(self):
        image = io.BytesIO()
        Image.new("RGB", (8, 8), color="blue").save(image, format="PNG")
        image.seek(0)
        image.name = "compatibility.png"

        upload_response = self.client.post("/api/v1/upload", {"files": image}, format="multipart")
        self.assertEqual(upload_response.status_code, 201)
        asset_id = upload_response.json()[0]["id"]

        create_response = self.client.post(
            "/api/v1/posts/user-create",
            {
                "data": {
                    "title": "Compatibility Post",
                    "content": "<p>Hello</p>",
                    "images": [asset_id],
                }
            },
            format="json",
        )
        self.assertEqual(create_response.status_code, 201)
        document_id = create_response.json()["data"]["documentId"]
        publish_response = self.client.post(f"/api/v1/posts/{document_id}/user-publish")
        self.assertEqual(publish_response.status_code, 200)
        self.assertEqual(publish_response.json()["data"]["author"]["documentId"], self.user.document_id)

        post = Post.objects.get(document_id=document_id)
        self.assertTrue(post.is_published)
        self.assertEqual(post.assets.count(), 1)
        self.assertEqual(MediaAsset.objects.count(), 1)

    def test_new_my_posts_endpoint_lists_owned_posts(self):
        Post.objects.create(title="Owned Post", excerpt="Excerpt", content="Body", author=self.user)
        response = self.client.get("/api/v1/me/posts/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), 1)
        self.assertEqual(response.json()[0]["author"]["document_id"], self.user.document_id)
        self.assertEqual(response.json()[0]["author"]["documentId"], self.user.document_id)

    def test_admin_seed_users_and_batch_delete(self):
        self.client.force_authenticate(self.admin)

        roles_response = self.client.get("/api/v1/admin/roles/")
        self.assertEqual(roles_response.status_code, 200)
        self.assertTrue(any(item["id"] == "user" for item in roles_response.json()["data"]))

        seed_response = self.client.post("/api/v1/admin/users/seed/", {"count": 3}, format="json")
        self.assertEqual(seed_response.status_code, 200)
        seeded_users = list(User.objects.filter(is_seeded=True).order_by("id"))
        self.assertGreaterEqual(len(seeded_users), 3)

        delete_response = self.client.post(
            "/api/v1/admin/users/seed/batch-delete/",
            {"ids": [seeded_users[0].id, seeded_users[1].id]},
            format="json",
        )
        self.assertEqual(delete_response.status_code, 200)
        self.assertEqual(delete_response.json()["data"]["deletedCount"], 2)

    @patch("trekky_apps.common.api_views.list_folder_tree")
    @patch("trekky_apps.common.api_views.list_assets")
    def test_admin_media_endpoints_return_cloudinary_payload(self, mock_list_assets, mock_list_folders):
        self.client.force_authenticate(self.admin)
        mock_list_folders.return_value = [
            {"name": "blog", "path": "blog", "children": [{"name": "hotels", "path": "blog/hotels", "children": []}]}
        ]
        mock_list_assets.return_value = {
            "items": [
                {
                    "id": 1,
                    "document_id": "doc_media_1",
                    "public_id": "blog/hotels/demo-image",
                    "folder": "blog/hotels",
                    "resource_type": "image",
                    "url": "https://example.com/demo-image.jpg",
                    "thumbnail_url": "https://example.com/demo-image.jpg",
                    "original_filename": "demo-image.jpg",
                    "mime_type": "image/jpeg",
                    "size_bytes": 12345,
                    "width": 1200,
                    "height": 800,
                    "created_at": "2026-03-28T10:00:00+07:00",
                }
            ],
            "next_cursor": "",
            "total_count": 1,
        }

        folders_response = self.client.get("/api/v1/admin/media/folders/")
        assets_response = self.client.get("/api/v1/admin/media/assets/?folder=blog%2Fhotels")

        self.assertEqual(folders_response.status_code, 200)
        self.assertEqual(assets_response.status_code, 200)
        self.assertEqual(folders_response.json()["items"][0]["path"], "blog")
        self.assertEqual(assets_response.json()["items"][0]["public_id"], "blog/hotels/demo-image")

    @patch("trekky_apps.common.api_views.upload_asset")
    @patch("trekky_apps.common.api_views.delete_asset")
    def test_admin_media_upload_and_delete_endpoints(self, mock_delete_asset, mock_upload_asset):
        self.client.force_authenticate(self.admin)
        mock_upload_asset.return_value = {
            "id": 10,
            "document_id": "doc_media_10",
            "public_id": "blog/uploaded-image",
            "folder": "blog",
            "resource_type": "image",
            "url": "https://example.com/uploaded-image.jpg",
            "thumbnail_url": "https://example.com/uploaded-image.jpg",
            "original_filename": "uploaded-image.jpg",
            "mime_type": "image/jpeg",
            "size_bytes": 999,
            "width": 640,
            "height": 480,
            "created_at": "2026-03-28T10:00:00+07:00",
        }
        mock_delete_asset.return_value = {"public_id": "blog/uploaded-image", "status": "deleted"}

        image = io.BytesIO()
        Image.new("RGB", (8, 8), color="green").save(image, format="PNG")
        image.seek(0)
        image.name = "upload-test.png"

        upload_response = self.client.post("/api/v1/admin/media/upload/", {"files": image, "folder": "blog"}, format="multipart")
        delete_response = self.client.post(
            "/api/v1/admin/media/delete/",
            {"public_id": "blog/uploaded-image", "resource_type": "image"},
            format="json",
        )

        self.assertEqual(upload_response.status_code, 201)
        self.assertEqual(delete_response.status_code, 200)
        self.assertEqual(upload_response.json()["items"][0]["folder"], "blog")
        self.assertEqual(delete_response.json()["status"], "deleted")
