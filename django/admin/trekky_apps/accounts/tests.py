from django.contrib.auth import get_user_model
from django.test import TestCase


User = get_user_model()


class UserModelTests(TestCase):
    def test_document_id_generated_for_user(self):
        user = User.objects.create_user(email="user-doc@example.com", username="userdoc", password="Secret123!")
        self.assertEqual(len(user.document_id), 24)
