from django.contrib.auth import get_user_model
from django.test import TestCase

from trekky_apps.taxonomy.models import Category

from .models import ModeratorCategoryAssignment


User = get_user_model()


class ModeratorAssignmentTests(TestCase):
    def test_unique_assignment(self):
        moderator = User.objects.create_user(
            email="mod@example.com",
            username="mod",
            password="secret123",
            role="moderator",
        )
        category = Category.objects.create(name="Hotels")
        ModeratorCategoryAssignment.objects.create(moderator=moderator, category=category)
        with self.assertRaises(Exception):
            ModeratorCategoryAssignment.objects.create(moderator=moderator, category=category)
