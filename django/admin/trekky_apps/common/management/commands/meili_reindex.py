from django.core.management.base import BaseCommand

from trekky_apps.common import search_service
from trekky_apps.content.models import Post
from trekky_apps.taxonomy.models import Category, Tag


class Command(BaseCommand):
    help = "Reindex all published posts, tags, and categories to MeiliSearch"

    def handle(self, *args, **options):
        client = search_service.get_client()
        if not client:
            self.stderr.write(self.style.ERROR(
                "MeiliSearch is not reachable. Check MEILISEARCH_URL and MEILISEARCH_API_KEY in .env"
            ))
            return

        self.stdout.write("Setting up indexes...")
        search_service.setup_indexes(client)

        # Posts
        posts = list(Post.objects.filter(is_published=True).prefetch_related("categories", "tags", "author"))
        self.stdout.write(f"Indexing {len(posts)} published posts...")
        if posts:
            docs = [search_service._post_document(p) for p in posts]
            client.index(search_service.INDEX_POSTS).add_documents(docs)
        self.stdout.write(self.style.SUCCESS(f"  OK {len(posts)} posts indexed"))

        # Tags
        tags = list(Tag.objects.all())
        self.stdout.write(f"Indexing {len(tags)} tags...")
        if tags:
            client.index(search_service.INDEX_TAGS).add_documents([search_service._tag_document(t) for t in tags])
        self.stdout.write(self.style.SUCCESS(f"  OK {len(tags)} tags indexed"))

        # Categories
        categories = list(Category.objects.all())
        self.stdout.write(f"Indexing {len(categories)} categories...")
        if categories:
            client.index(search_service.INDEX_CATEGORIES).add_documents([search_service._category_document(c) for c in categories])
        self.stdout.write(self.style.SUCCESS(f"  OK {len(categories)} categories indexed"))

        self.stdout.write(self.style.SUCCESS("Reindex complete."))
