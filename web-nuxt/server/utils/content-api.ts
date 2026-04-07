import type { Category, Comment, PaginatedResponse, Post, StrapiPage, Tag } from "../../shared/types";

const configApiUrl = () => getDjangoUrl();
const apiBase = () => `${configApiUrl()}/api/v1`;

type DjangoCategory = {
  document_id: string;
  name: string;
  slug: string;
  description?: string;
  sort_order?: number;
  parent?: number | string | null;
};

type DjangoTag = {
  document_id: string;
  name: string;
  slug: string;
  description?: string;
};

type DjangoUser = {
  id: number;
  email: string;
  username: string;
  bio?: string | null;
  avatar?: string | null;
};

type DjangoAsset = {
  id: number;
  url: string;
  alt_text?: string | null;
  mime_type?: string | null;
  width?: number | null;
  height?: number | null;
};

type DjangoPost = {
  id?: number;
  document_id: string;
  title: string;
  slug: string;
  excerpt?: string;
  content: string;
  author?: DjangoUser | null;
  categories?: DjangoCategory[];
  tags?: DjangoTag[];
  assets?: DjangoAsset[];
  is_published?: boolean;
  published_at?: string | null;
  created_at?: string;
  updated_at?: string;
};

type DjangoPage = {
  document_id: string;
  title: string;
  slug: string;
  type: string;
  content?: string | null;
};

type DjangoComment = {
  id: number;
  document_id: string;
  target_type: string;
  target_document_id: string;
  parent?: number | null;
  author?: DjangoUser | null;
  author_name?: string;
  content: string;
  created_at?: string;
};

type DRFList<T> = {
  count: number;
  next: string | null;
  previous: string | null;
  results: T[];
};

async function djangoFetch<T>(path: string, noStore = false): Promise<T> {
  const response = await fetch(`${apiBase()}${path}`, {
    headers: { "content-type": "application/json" },
    cache: noStore ? "no-store" : undefined,
  });
  if (!response.ok) throw createError({ statusCode: response.status, statusMessage: `Django request failed: ${path}` });
  return response.json() as Promise<T>;
}

function extractList<T>(payload: DRFList<T> | T[]): T[] {
  return Array.isArray(payload) ? payload : payload.results ?? [];
}

function toAbsoluteUrl(url: string | null | undefined) {
  if (!url) return null;
  if (url.startsWith("http://") || url.startsWith("https://")) return url;
  return `${configApiUrl()}${url}`;
}

function normalizePost(raw: DjangoPost): Post {
  return {
    id: raw.id ?? 0,
    documentId: raw.document_id,
    title: raw.title,
    slug: raw.slug,
    excerpt: raw.excerpt,
    content: raw.content,
    categories: (raw.categories ?? []).map((category) => ({
      id: 0,
      documentId: category.document_id,
      name: category.name,
      slug: category.slug,
      description: category.description,
    })),
    tags: (raw.tags ?? []).map((tag) => ({
      id: 0,
      documentId: tag.document_id,
      name: tag.name,
      slug: tag.slug,
      description: tag.description,
    })),
    images: (raw.assets ?? []).map((asset) => ({
      id: asset.id,
      url: toAbsoluteUrl(asset.url) ?? "",
      mime: asset.mime_type ?? null,
      alternativeText: asset.alt_text ?? null,
      width: asset.width ?? undefined,
      height: asset.height ?? undefined,
    })),
    author: raw.author
      ? {
          id: raw.author.id,
          username: raw.author.username,
          avatar: raw.author.avatar ? { id: 0, url: toAbsoluteUrl(raw.author.avatar) ?? "" } : null,
        }
      : undefined,
    createdAt: raw.created_at,
    updatedAt: raw.updated_at,
    publishedAt: raw.published_at ?? undefined,
    status: raw.is_published ? "published" : "draft",
  };
}

function normalizePage(raw: DjangoPage): StrapiPage {
  return {
    id: 0,
    documentId: raw.document_id,
    title: raw.title,
    slug: raw.slug,
    type: raw.type as StrapiPage["type"],
    content: raw.content ?? null,
  };
}

function normalizeComment(raw: DjangoComment, idToDocId: Map<number, string>): Comment {
  const parentDocId = raw.parent != null ? idToDocId.get(raw.parent) : undefined;
  return {
    id: raw.id,
    documentId: raw.document_id,
    authorName: raw.author?.username ?? raw.author_name ?? "Anonymous",
    authorAvatarUrl: raw.author?.avatar ? toAbsoluteUrl(raw.author.avatar) : null,
    content: raw.content,
    targetType: raw.target_type as Comment["targetType"],
    targetDocumentId: raw.target_document_id,
    createdAt: raw.created_at ?? "",
    parent: parentDocId ? { documentId: parentDocId } : null,
  };
}

function toPaginatedResponse(posts: Post[], total: number, page: number, pageSize: number): PaginatedResponse<Post> {
  return {
    data: posts,
    meta: {
      pagination: {
        page,
        pageSize,
        pageCount: Math.max(1, Math.ceil(total / pageSize)),
        total,
      },
    },
  };
}

export async function getPostsWithPagination(page = 1, pageSize = 10, categorySlug?: string, tagSlug?: string, authorUsername?: string) {
  if (authorUsername) return getPostsByUsername(authorUsername, page, pageSize);

  const params = new URLSearchParams({
    ordering: "-created_at",
    page: String(page),
    page_size: String(pageSize),
  });

  if (categorySlug) {
    const ids = await getCategorySubtreeDocumentIds(categorySlug);
    if (ids.length === 0) return toPaginatedResponse([], 0, page, pageSize);
    params.set("categories__document_id", ids[0]);
  }

  if (tagSlug) {
    const tag = await getTagBySlug(tagSlug);
    if (!tag) return toPaginatedResponse([], 0, page, pageSize);
    params.set("tags__document_id", tag.documentId);
  }

  const payload = await djangoFetch<DRFList<DjangoPost> | DjangoPost[]>(`/public/posts/?${params.toString()}`);
  const posts = extractList(payload).map(normalizePost);
  const total = Array.isArray(payload) ? posts.length : payload.count;
  return toPaginatedResponse(posts, total, page, pageSize);
}

export async function getPostsByUsername(username: string, page = 1, pageSize = 10) {
  const payload = await djangoFetch<{ user?: unknown; results?: DjangoPost[] }>(
    `/public/users/${encodeURIComponent(username)}/posts/`,
  );
  const allPosts = (payload.results ?? []).map(normalizePost);
  const total = allPosts.length;
  const start = (page - 1) * pageSize;
  return toPaginatedResponse(allPosts.slice(start, start + pageSize), total, page, pageSize);
}

export async function getCategoryBySlug(slug: string): Promise<Category | null> {
  const payload = await djangoFetch<DRFList<DjangoCategory> | DjangoCategory[]>("/public/categories/?page_size=1000");
  const rows = extractList(payload);
  const category = rows.find((item) => item.slug === slug);
  if (!category) return null;

  const children = rows
    .filter((item) => item.parent != null && String(item.parent) === category.document_id)
    .map((item) => ({
      id: 0,
      documentId: item.document_id,
      name: item.name,
      slug: item.slug,
    }));

  const parentRaw = category.parent != null ? rows.find((item) => item.document_id === String(category.parent)) : null;
  return {
    id: 0,
    documentId: category.document_id,
    name: category.name,
    slug: category.slug,
    description: category.description,
    parent: parentRaw ? { documentId: parentRaw.document_id, name: parentRaw.name, slug: parentRaw.slug } : null,
    children,
  };
}

export async function getTagBySlug(slug: string): Promise<Tag | null> {
  const payload = await djangoFetch<DRFList<DjangoTag> | DjangoTag[]>(`/public/tags/?slug=${encodeURIComponent(slug)}`);
  const tags = extractList(payload);
  if (tags.length === 0) return null;
  const tag = tags[0];
  return { id: 0, documentId: tag.document_id, name: tag.name, slug: tag.slug, description: tag.description };
}

export async function getPostBySlug(slug: string): Promise<Post | null> {
  const payload = await djangoFetch<DRFList<DjangoPost> | DjangoPost[]>(`/public/posts/?slug=${encodeURIComponent(slug)}`);
  const posts = extractList(payload);
  return posts[0] ? normalizePost(posts[0]) : null;
}

export async function getPostByDocumentId(documentId: string): Promise<Post | null> {
  try {
    const raw = await djangoFetch<DjangoPost>(`/public/posts/${encodeURIComponent(documentId)}/`, true);
    return normalizePost(raw);
  } catch {
    return null;
  }
}

function parsePostRouteId(routeId: string) {
  const trimmed = routeId.trim();
  if (!trimmed) return { slug: "", documentId: "" };
  if (!trimmed.includes("--")) return { slug: trimmed, documentId: trimmed };
  const parts = trimmed.split("--");
  const documentId = parts.pop()?.trim() ?? "";
  return { slug: parts.join("--").trim(), documentId };
}

export async function getPostByRouteId(routeId: string) {
  const { slug, documentId } = parsePostRouteId(routeId);
  if (documentId) {
    const byId = await getPostByDocumentId(documentId);
    if (byId) return byId;
  }
  return slug ? getPostBySlug(slug) : null;
}

export async function getCommentsForTarget(targetType: Comment["targetType"], targetDocumentId: string) {
  const payload = await djangoFetch<DRFList<DjangoComment> | DjangoComment[]>(
    `/public/comments/?target_type=${encodeURIComponent(targetType)}&target_document_id=${encodeURIComponent(targetDocumentId)}&ordering=created_at`,
    true,
  );
  const rows = extractList(payload);
  const idToDocId = new Map<number, string>();
  rows.forEach((comment) => {
    idToDocId.set(comment.id, comment.document_id);
  });
  return rows.map((comment) => normalizeComment(comment, idToDocId));
}

export async function getPageByType(type: "home" | "footer"): Promise<StrapiPage | null> {
  try {
    const payload = await djangoFetch<DRFList<DjangoPage> | DjangoPage[]>(`/public/pages/?type=${type}&page_size=1`, true);
    const rows = extractList(payload);
    return rows[0] ? normalizePage(rows[0]) : null;
  } catch {
    return null;
  }
}

export async function getPageBySlug(slug: string): Promise<StrapiPage | null> {
  try {
    const payload = await djangoFetch<DRFList<DjangoPage> | DjangoPage[]>(
      `/public/pages/?slug=${encodeURIComponent(slug)}&page_size=1`,
      true,
    );
    const rows = extractList(payload);
    return rows[0] ? normalizePage(rows[0]) : null;
  } catch {
    return null;
  }
}

export async function getFooterPages(): Promise<StrapiPage[]> {
  try {
    const payload = await djangoFetch<DRFList<DjangoPage> | DjangoPage[]>("/public/pages/?type=footer&ordering=title&page_size=50", true);
    return extractList(payload).map(normalizePage);
  } catch {
    return [];
  }
}

export async function getSidebarData(): Promise<{ topPosts: Post[]; topTags: Tag[] }> {
  try {
    const [postsPayload, commentsPayload] = await Promise.all([
      djangoFetch<DRFList<DjangoPost> | DjangoPost[]>("/public/posts/?ordering=-published_at&page_size=1000", true),
      djangoFetch<DRFList<DjangoComment> | DjangoComment[]>("/public/comments/?target_type=post&page_size=1000", true),
    ]);

    const posts = extractList(postsPayload)
      .map(normalizePost)
      .filter((post) => post.documentId && post.slug && post.status === "published");

    const commentCounts = new Map<string, number>();
    extractList(commentsPayload).forEach((comment) => {
      if (!comment.target_document_id) return;
      commentCounts.set(comment.target_document_id, (commentCounts.get(comment.target_document_id) ?? 0) + 1);
    });

    const now = Date.now();
    const halfLifeDays = 30;
    const rankedPosts = posts
      .map((post) => {
        const commentsCount = commentCounts.get(post.documentId) ?? 0;
        const publishedAt = post.publishedAt ?? post.createdAt ?? null;
        const ageMs = publishedAt ? Math.max(0, now - new Date(publishedAt).getTime()) : 0;
        const ageDays = ageMs / (1000 * 60 * 60 * 24);
        const decay = Math.pow(0.5, ageDays / halfLifeDays);
        const score = commentsCount * decay;
        return {
          ...post,
          commentsCount,
          score,
          sortDate: publishedAt ? new Date(publishedAt).getTime() : 0,
        };
      })
      .sort((a, b) => {
        if (b.score !== a.score) return b.score - a.score;
        if ((b.commentsCount ?? 0) !== (a.commentsCount ?? 0)) return (b.commentsCount ?? 0) - (a.commentsCount ?? 0);
        return b.sortDate - a.sortDate;
      })
      .slice(0, 5)
      .map(({ score: _score, sortDate: _sortDate, ...post }) => post);

    const tagStats = new Map<string, Tag>();
    posts.forEach((post) => {
      (post.tags ?? []).forEach((tag) => {
        const existing = tagStats.get(tag.documentId);
        if (existing) {
          existing.postsCount = (existing.postsCount ?? 0) + 1;
          return;
        }
        tagStats.set(tag.documentId, {
          ...tag,
          postsCount: 1,
        });
      });
    });

    const topTags = Array.from(tagStats.values())
      .filter((tag) => tag.slug)
      .sort((a, b) => {
        if ((b.postsCount ?? 0) !== (a.postsCount ?? 0)) return (b.postsCount ?? 0) - (a.postsCount ?? 0);
        return a.name.localeCompare(b.name, "vi");
      })
      .slice(0, 20);

    return { topPosts: rankedPosts, topTags };
  } catch {
    return { topPosts: [], topTags: [] };
  }
}

export async function getPostsForSitemap() {
  return getAllEntriesForSitemap("/public/posts/?ordering=-updated_at&page_size=1000");
}

export async function getCategoriesForSitemap() {
  return getAllEntriesForSitemap("/public/categories/?ordering=-updated_at&page_size=1000");
}

export async function getTagsForSitemap() {
  return getAllEntriesForSitemap("/public/tags/?ordering=-updated_at&page_size=1000");
}

export async function getPagesForSitemap() {
  return getAllEntriesForSitemap("/public/pages/?type=footer&ordering=-updated_at&page_size=1000");
}

async function getCategorySubtreeDocumentIds(categorySlug: string): Promise<string[]> {
  const payload = await djangoFetch<DRFList<DjangoCategory> | DjangoCategory[]>("/public/categories/?page_size=1000");
  const rows = extractList(payload);
  const root = rows.find((item) => item.slug === categorySlug);
  if (!root) return [];

  const childrenByParent = new Map<string, string[]>();
  rows.forEach((item) => {
    if (item.parent == null) return;
    const key = String(item.parent);
    const bucket = childrenByParent.get(key) ?? [];
    bucket.push(item.document_id);
    childrenByParent.set(key, bucket);
  });

  const visited: string[] = [];
  const queue = [root.document_id];
  while (queue.length) {
    const current = queue.shift()!;
    if (visited.includes(current)) continue;
    visited.push(current);
    (childrenByParent.get(current) ?? []).forEach((child) => queue.push(child));
  }

  return visited;
}

type SitemapEntry = {
  slug: string;
  documentId?: string;
  updatedAt?: string;
};

async function getAllEntriesForSitemap(path: string): Promise<SitemapEntry[]> {
  try {
    const payload = await djangoFetch<DRFList<Record<string, unknown>> | Record<string, unknown>[]>(path);
    return extractList(payload).map((row) => ({
      slug: String(row.slug ?? row.document_id ?? ""),
      documentId: String(row.document_id ?? ""),
      updatedAt: String(row.updated_at ?? row.updatedAt ?? ""),
    }));
  } catch {
    return [];
  }
}
