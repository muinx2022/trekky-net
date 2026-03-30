from django.db.models.signals import m2m_changed, post_delete, post_save
from django.dispatch import receiver

from trekky_apps.common import search_service

from .models import Post


@receiver(post_save, sender=Post)
def sync_post_to_meili(sender, instance, **kwargs):
    if instance.is_published:
        search_service.index_post(instance)
    else:
        search_service.delete_post(instance.id)


@receiver(post_delete, sender=Post)
def remove_post_from_meili(sender, instance, **kwargs):
    search_service.delete_post(instance.id)


@receiver(m2m_changed, sender=Post.categories.through)
@receiver(m2m_changed, sender=Post.tags.through)
def sync_post_m2m_to_meili(sender, instance, action, **kwargs):
    if action in ("post_add", "post_remove", "post_clear"):
        if isinstance(instance, Post) and instance.is_published:
            search_service.index_post(instance)
