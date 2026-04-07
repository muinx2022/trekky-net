"""
MeiliSearch integration service.
Provides indexing and search for Posts, Tags, and Categories.
Falls back to DB queries if MeiliSearch is unavailable or not configured.
"""
import logging

from django.conf import settings
from django.db.models import Q

logger = logging.getLogger(__name__)

INDEX_POSTS = "posts"
INDEX_TAGS = "tags"
INDEX_CATEGORIES = "categories"


def get_client():
    """Return a MeiliSearch client or None if not configured."""
    url = getattr(settings, "MEILISEARCH_URL", "")
    key = getattr(settings, "MEILISEARCH_API_KEY", "")
    if not url:
        return None
    try:
        import meilisearch
        client = meilisearch.Client(url, key or None)
        client.health()
        return client
    except Exception:
        return None


def setup_indexes(client=None):
    """Create indexes and configure their attributes."""
    client = client or get_client()
    if not client:
        return

    # Posts index
    try:
        client.create_index(INDEX_POSTS, {"primaryKey": "id"})
    except Exception:
        pass
    try:
        client.index(INDEX_POSTS).update_searchable_attributes(["title", "excerpt", "content", "author_username", "categories", "tags"])
        client.index(INDEX_POSTS).update_filterable_attributes(["is_published", "document_id"])
        client.index(INDEX_POSTS).update_sortable_attributes(["published_at"])
    except Exception as e:
        logger.warning("MeiliSearch: failed to configure posts index: %s", e)

    # Tags index
    try:
        client.create_index(INDEX_TAGS, {"primaryKey": "id"})
    except Exception:
        pass
    try:
        client.index(INDEX_TAGS).update_searchable_attributes(["name", "description"])
    except Exception as e:
        logger.warning("MeiliSearch: failed to configure tags index: %s", e)

    # Categories index
    try:
        client.create_index(INDEX_CATEGORIES, {"primaryKey": "id"})
    except Exception:
        pass
    try:
        client.index(INDEX_CATEGORIES).update_searchable_attributes(["name", "description"])
    except Exception as e:
        logger.warning("MeiliSearch: failed to configure categories index: %s", e)


def _post_document(post):
    return {
        "id": post.id,
        "document_id": post.document_id,
        "title": post.title,
        "slug": post.slug,
        "excerpt": post.excerpt or "",
        "content": post.content or "",
        "author_username": post.author.username if post.author else "",
        "categories": [c.name for c in post.categories.all()],
        "tags": [t.name for t in post.tags.all()],
        "published_at": post.published_at.isoformat() if post.published_at else None,
    }


def _tag_document(tag):
    return {
        "id": tag.id,
        "document_id": tag.document_id,
        "name": tag.name,
        "slug": tag.slug,
        "description": tag.description or "",
    }


def _category_document(category):
    return {
        "id": category.id,
        "document_id": category.document_id,
        "name": category.name,
        "slug": category.slug,
        "description": category.description or "",
    }


def index_post(post):
    client = get_client()
    if not client:
        return
    try:
        client.index(INDEX_POSTS).add_documents([_post_document(post)])
    except Exception as e:
        logger.warning("MeiliSearch: failed to index post %s: %s", post.id, e)


def delete_post(post_id):
    client = get_client()
    if not client:
        return
    try:
        client.index(INDEX_POSTS).delete_document(post_id)
    except Exception as e:
        logger.warning("MeiliSearch: failed to delete post %s: %s", post_id, e)


def index_tag(tag):
    client = get_client()
    if not client:
        return
    try:
        client.index(INDEX_TAGS).add_documents([_tag_document(tag)])
    except Exception as e:
        logger.warning("MeiliSearch: failed to index tag %s: %s", tag.id, e)


def delete_tag(tag_id):
    client = get_client()
    if not client:
        return
    try:
        client.index(INDEX_TAGS).delete_document(tag_id)
    except Exception as e:
        logger.warning("MeiliSearch: failed to delete tag %s: %s", tag_id, e)


def index_category(category):
    client = get_client()
    if not client:
        return
    try:
        client.index(INDEX_CATEGORIES).add_documents([_category_document(category)])
    except Exception as e:
        logger.warning("MeiliSearch: failed to index category %s: %s", category.id, e)


def delete_category(category_id):
    client = get_client()
    if not client:
        return
    try:
        client.index(INDEX_CATEGORIES).delete_document(category_id)
    except Exception as e:
        logger.warning("MeiliSearch: failed to delete category %s: %s", category_id, e)


def _db_fallback(q):
    """Search via DB when MeiliSearch is unavailable."""
    from trekky_apps.content.models import Post
    from trekky_apps.taxonomy.models import Category, Tag

    posts = list(
        Post.objects.filter(is_published=True)
        .filter(
            Q(title__icontains=q)
            | Q(excerpt__icontains=q)
            | Q(content__icontains=q)
            | Q(author__username__icontains=q)
            | Q(categories__name__icontains=q)
            | Q(tags__name__icontains=q)
        )
        .distinct()
        .values("id", "document_id", "title", "slug", "excerpt")[:10]
    )
    tags = list(
        Tag.objects.filter(Q(name__icontains=q) | Q(description__icontains=q) | Q(aliases__icontains=q))
        .values("id", "document_id", "name", "slug", "description")[:5]
    )
    categories = list(
        Category.objects.filter(Q(name__icontains=q) | Q(description__icontains=q))
        .values("id", "document_id", "name", "slug", "description")[:5]
    )
    return {"posts": posts, "tags": tags, "categories": categories}


def search(q, post_limit=10, tag_limit=5, category_limit=5):
    """Search across posts, tags and categories. Falls back to DB if MeiliSearch unavailable."""
    if not q:
        return {"posts": [], "tags": [], "categories": []}

    client = get_client()
    if not client:
        return _db_fallback(q)

    try:
        results = client.multi_search([
            {"indexUid": INDEX_POSTS, "q": q, "limit": post_limit, "attributesToRetrieve": ["id", "document_id", "documentId", "title", "slug", "excerpt"]},
            {"indexUid": INDEX_TAGS, "q": q, "limit": tag_limit, "attributesToRetrieve": ["id", "document_id", "documentId", "name", "slug", "description"]},
            {"indexUid": INDEX_CATEGORIES, "q": q, "limit": category_limit, "attributesToRetrieve": ["id", "document_id", "documentId", "name", "slug", "description"]},
        ])
        hits = results.get("results", [])
        payload = {
            "posts": hits[0].get("hits", []) if len(hits) > 0 else [],
            "tags": hits[1].get("hits", []) if len(hits) > 1 else [],
            "categories": hits[2].get("hits", []) if len(hits) > 2 else [],
        }
        if not payload["posts"] and not payload["tags"] and not payload["categories"]:
            logger.info("MeiliSearch: zero hits for query '%s', falling back to DB search", q)
            return _db_fallback(q)
        return payload
    except Exception as e:
        logger.warning("MeiliSearch: search failed, falling back to DB: %s", e)
        return _db_fallback(q)
