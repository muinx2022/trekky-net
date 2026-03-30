from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver

from trekky_apps.common import search_service

from .models import Category, Tag


@receiver(post_save, sender=Tag)
def sync_tag_to_meili(sender, instance, **kwargs):
    search_service.index_tag(instance)


@receiver(post_delete, sender=Tag)
def remove_tag_from_meili(sender, instance, **kwargs):
    search_service.delete_tag(instance.id)


@receiver(post_save, sender=Category)
def sync_category_to_meili(sender, instance, **kwargs):
    search_service.index_category(instance)


@receiver(post_delete, sender=Category)
def remove_category_from_meili(sender, instance, **kwargs):
    search_service.delete_category(instance.id)
