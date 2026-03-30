// Django backend API client (replaces Strapi client)
const DJANGO_URL = (process.env.STRAPI_INTERNAL_URL ?? process.env.NEXT_PUBLIC_API_URL ?? "http://127.0.0.1:8000")
  .replace("http://localhost:8000", "http://127.0.0.1:8000");
const API_BASE = `${DJANGO_URL}/api/v1`;

// ─── Exported types (kept compatible with Strapi frontend) ───────────────────

export type Category = {
  id: number;
  documentId: string;
  name: string;
  slug: string;
  description?: string;
  parent?: {
    documentId: string;
    name: string;
    slug: string;
  } | null;
  children?: Category[];
};

export type Tag = {
  id: number;
  documentId: string;
  name: string;
  slug: string;
  description?: string;
};

export type Comment = {
  id: number;
  documentId: string;
  authorName: string;
  authorAvatarUrl?: string | null;
  content: string;
  targetType: "post" | "page" | "product" | "other";
  targetDocumentId: string;
  createdAt: string;
  parent?: { documentId: string } | null;
};

export type StrapiImage = {
  id: number;
  url: string;
  mime?: string | null;
  alternativeText?: string | null;
  width?: number;
  height?: number;
  name?: string;
};

export type PostAuthor = {
  id: number;
  username: string;
  avatar?: StrapiImage | null;
};

export type Post = {
  id: number;
  documentId: string;
  title: string;
  slug: string;
  excerpt?: string;
  content: string;
  categories?: Category[];
  tags?: Tag[];
  images?: StrapiImage[];
  author?: PostAuthor;
  createdAt?: string;
  updatedAt?: string;
  publishedAt?: string;
  status?: "draft" | "published";
  commentsCount?: number;
  likesCount?: number;
};

export type StrapiPage = {
  id: number;
  documentId: string;
  title: string;
  slug: string;
  type: "home" | "footer";
  content?: string | null;
};

// ─── Django raw types ────────────────────────────────────────────────────────

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
  role?: string;
  bio?: string | null;
  avatar?: string | null;
};

type DjangoAsset = {
  id: number;
  media_id?: number;
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
  permalink?: string;
};

type DjangoPage = {
  document_id: string;
  title: string;
  slug: string;
  type: string;
  content?: string | null;
  is_published?: boolean;
  published_at?: string | null;
  created_at?: string;
  updated_at?: string;
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
  status?: string;
  created_at?: string;
  updated_at?: string;
};

type DRFPaginatedList<T> = {
  count: number;
  next: string | null;
  previous: string | null;
  results: T[];
};

// ─── Fetch helpers ───────────────────────────────────────────────────────────

async function djangoFetch<T>(path: string): Promise<T> {
  let response: Response;
  try {
    response = await fetch(`${API_BASE}${path}`, {
      headers: { "Content-Type": "application/json" },
      next: { revalidate: 30 },
    });
  } catch (error) {
    console.error(`Failed to fetch from Django at ${API_BASE}${path}:`, error);
    throw new Error(`Failed to connect to Django API at ${DJANGO_URL}`);
  }
  if (!response.ok) {
    throw new Error(`Django request failed: ${response.status} ${path}`);
  }
  return response.json() as Promise<T>;
}

async function djangoFetchNoStore<T>(path: string): Promise<T> {
  let response: Response;
  try {
    response = await fetch(`${API_BASE}${path}`, {
      headers: { "Content-Type": "application/json" },
      cache: "no-store",
    });
  } catch (error) {
    console.error(`Failed to fetch from Django at ${API_BASE}${path}:`, error);
    throw new Error(`Failed to connect to Django API at ${DJANGO_URL}`);
  }
  if (!response.ok) {
    throw new Error(`Django request failed: ${response.status} ${path}`);
  }
  return response.json() as Promise<T>;
}

// ─── Normalizers ─────────────────────────────────────────────────────────────

function toAbsoluteUrl(url: string | null | undefined): string | null {
  if (!url) return null;
  if (url.startsWith("http://") || url.startsWith("https://")) return url;
  return `${DJANGO_URL}${url}`;
}

function normalizePost(raw: DjangoPost): Post {
  const categories = (raw.categories ?? []).map((c) => ({
    id: 0,
    documentId: c.document_id,
    name: c.name,
    slug: c.slug,
  }));

  const tags = (raw.tags ?? []).map((t) => ({
    id: 0,
    documentId: t.document_id,
    name: t.name,
    slug: t.slug,
  }));

  const images: StrapiImage[] = (raw.assets ?? []).map((a) => ({
    id: a.id,
    url: toAbsoluteUrl(a.url) ?? "",
    mime: a.mime_type ?? null,
    alternativeText: a.alt_text ?? null,
    width: a.width ?? undefined,
    height: a.height ?? undefined,
  }));

  const author: PostAuthor | undefined = raw.author
    ? {
        id: raw.author.id,
        username: raw.author.username,
        avatar: raw.author.avatar
          ? { id: 0, url: toAbsoluteUrl(raw.author.avatar) ?? "" }
          : null,
      }
    : undefined;

  return {
    id: raw.id ?? 0,
    documentId: raw.document_id,
    title: raw.title,
    slug: raw.slug,
    excerpt: raw.excerpt,
    content: raw.content,
    categories,
    tags,
    images,
    author,
    createdAt: raw.created_at,
    updatedAt: raw.updated_at,
    publishedAt: raw.published_at ?? undefined,
    status: raw.is_published ? "published" : "draft",
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

function toPaginatedResponse(posts: Post[], total: number, page: number, pageSize: number) {
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

function extractList<T>(payload: DRFPaginatedList<T> | T[]): T[] {
  if (Array.isArray(payload)) return payload;
  return (payload as DRFPaginatedList<T>).results ?? [];
}

// ─── Public API functions ─────────────────────────────────────────────────────

export async function getPosts() {
  const payload = await djangoFetch<DRFPaginatedList<DjangoPost> | DjangoPost[]>(
    "/public/posts/?ordering=-created_at&page_size=20",
  );
  return extractList(payload).map(normalizePost);
}

export async function getTopLevelCategories() {
  const payload = await djangoFetch<DRFPaginatedList<DjangoCategory> | DjangoCategory[]>(
    "/public/categories/?page_size=1000",
  );
  return extractList(payload)
    .map((c) => ({
      id: 0,
      documentId: c.document_id,
      name: c.name,
      slug: c.slug,
      description: c.description,
      parent: c.parent != null ? { documentId: String(c.parent), name: "", slug: "" } : null,
    }))
    .filter((c) => !c.parent) as Category[];
}

export async function getTopTags(limit: number = 12) {
  const payload = await djangoFetch<DRFPaginatedList<DjangoTag> | DjangoTag[]>(
    `/public/tags/?page_size=${limit}`,
  );
  return extractList(payload)
    .slice(0, limit)
    .map((t) => ({
      id: 0,
      documentId: t.document_id,
      name: t.name,
      slug: t.slug,
      description: t.description,
    })) as Tag[];
}

export async function getTopPosts(limit: number = 10) {
  const payload = await djangoFetch<DRFPaginatedList<DjangoPost> | DjangoPost[]>(
    `/public/posts/?ordering=-created_at&page_size=${limit}`,
  );
  return extractList(payload).map(normalizePost);
}

export async function getPublishedPostsCount() {
  const payload = await djangoFetchNoStore<DRFPaginatedList<DjangoPost> | DjangoPost[]>(
    "/public/posts/?page=1&page_size=1",
  );
  if (Array.isArray(payload)) return payload.length;
  return (payload as DRFPaginatedList<DjangoPost>).count ?? 0;
}

export async function getPostsWithPagination(
  page: number = 1,
  pageSize: number = 10,
  categorySlug?: string,
  tagSlug?: string,
  authorUsername?: string,
) {
  if (authorUsername) {
    return getPostsByUsername(authorUsername, page, pageSize);
  }

  const params = new URLSearchParams({
    ordering: "-created_at",
    page: String(page),
    page_size: String(pageSize),
  });

  if (categorySlug) {
    const categoryDocIds = await getCategorySubtreeDocumentIds(categorySlug);
    if (categoryDocIds.length === 0) {
      return toPaginatedResponse([], 0, page, pageSize);
    }
    // Use root category's document_id for filtering
    params.set("categories__document_id", categoryDocIds[0]);
  }

  if (tagSlug) {
    const tag = await getTagBySlug(tagSlug);
    if (!tag) return toPaginatedResponse([], 0, page, pageSize);
    params.set("tags__document_id", tag.documentId);
  }

  const payload = await djangoFetch<DRFPaginatedList<DjangoPost> | DjangoPost[]>(
    `/public/posts/?${params.toString()}`,
  );

  const posts = extractList(payload).map(normalizePost);
  const total = Array.isArray(payload) ? posts.length : (payload as DRFPaginatedList<DjangoPost>).count;

  return toPaginatedResponse(posts, total, page, pageSize);
}

export async function getPostsByUsername(
  username: string,
  page: number = 1,
  pageSize: number = 10,
) {
  const payload = await djangoFetch<{ user?: unknown; results?: DjangoPost[] }>(
    `/public/users/${encodeURIComponent(username)}/posts/`,
  );
  const allPosts = (payload.results ?? []).map(normalizePost);
  const total = allPosts.length;
  const start = (page - 1) * pageSize;
  const posts = allPosts.slice(start, start + pageSize);
  return toPaginatedResponse(posts, total, page, pageSize);
}

export async function getPostBySlug(slug: string) {
  const payload = await djangoFetch<DRFPaginatedList<DjangoPost> | DjangoPost[]>(
    `/public/posts/?slug=${encodeURIComponent(slug)}`,
  );
  const posts = extractList(payload);
  return posts.length > 0 ? normalizePost(posts[0]) : null;
}

export async function getPostByDocumentId(documentId: string) {
  try {
    const raw = await djangoFetchNoStore<DjangoPost>(
      `/public/posts/${encodeURIComponent(documentId)}/`,
    );
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
  const slug = parts.join("--").trim();
  return { slug, documentId };
}

export async function getPostByRouteId(routeId: string) {
  const { slug, documentId } = parsePostRouteId(routeId);
  if (documentId) {
    const byDocId = await getPostByDocumentId(documentId);
    if (byDocId) return byDocId;
  }
  if (slug) return getPostBySlug(slug);
  return null;
}

export async function getCategoryBySlug(slug: string) {
  const payload = await djangoFetch<DRFPaginatedList<DjangoCategory> | DjangoCategory[]>(
    "/public/categories/?page_size=1000",
  );
  const rows = extractList(payload);

  const category = rows.find((c) => c.slug === slug) ?? null;
  if (!category) return null;

  const children = rows
    .filter((c) => c.parent != null && String(c.parent) === category.document_id)
    .map((c) => ({ id: 0, documentId: c.document_id, name: c.name, slug: c.slug })) as Category[];

  const parentRaw = category.parent != null
    ? rows.find((c) => c.document_id === String(category.parent)) ?? null
    : null;

  return {
    id: 0,
    documentId: category.document_id,
    name: category.name,
    slug: category.slug,
    description: category.description,
    parent: parentRaw
      ? { documentId: parentRaw.document_id, name: parentRaw.name, slug: parentRaw.slug }
      : null,
    children,
  } as Category;
}

export async function getTagBySlug(slug: string) {
  const payload = await djangoFetch<DRFPaginatedList<DjangoTag> | DjangoTag[]>(
    `/public/tags/?slug=${encodeURIComponent(slug)}`,
  );
  const tags = extractList(payload);
  if (tags.length === 0) return null;
  const t = tags[0];
  return { id: 0, documentId: t.document_id, name: t.name, slug: t.slug } as Tag;
}

export async function getCommentsForTarget(
  targetType: Comment["targetType"],
  targetDocumentId: string,
) {
  const payload = await djangoFetchNoStore<DRFPaginatedList<DjangoComment> | DjangoComment[]>(
    `/public/comments/?target_type=${encodeURIComponent(targetType)}&target_document_id=${encodeURIComponent(targetDocumentId)}&ordering=created_at`,
  );
  const rawComments = extractList(payload);

  const idToDocId = new Map<number, string>();
  for (const c of rawComments) {
    if (c.id && c.document_id) idToDocId.set(c.id, c.document_id);
  }

  return rawComments.map((c) => normalizeComment(c, idToDocId));
}

export async function getPageByType(type: "home" | "footer"): Promise<StrapiPage | null> {
  try {
    const payload = await djangoFetchNoStore<DRFPaginatedList<DjangoPage> | DjangoPage[]>(
      `/public/pages/?type=${type}&page_size=1`,
    );
    const pages = extractList(payload);
    return pages.length > 0 ? normalizePage(pages[0]) : null;
  } catch {
    return null;
  }
}

export async function getFooterPages(): Promise<StrapiPage[]> {
  try {
    const payload = await djangoFetchNoStore<DRFPaginatedList<DjangoPage> | DjangoPage[]>(
      "/public/pages/?type=footer&ordering=title&page_size=50",
    );
    return extractList(payload).map(normalizePage);
  } catch {
    return [];
  }
}

export async function getPageBySlug(slug: string): Promise<StrapiPage | null> {
  try {
    const payload = await djangoFetchNoStore<DRFPaginatedList<DjangoPage> | DjangoPage[]>(
      `/public/pages/?slug=${encodeURIComponent(slug)}&page_size=1`,
    );
    const pages = extractList(payload);
    return pages.length > 0 ? normalizePage(pages[0]) : null;
  } catch {
    return null;
  }
}

// ─── Category subtree helper ─────────────────────────────────────────────────

async function getCategorySubtreeDocumentIds(categorySlug: string): Promise<string[]> {
  const payload = await djangoFetch<DRFPaginatedList<DjangoCategory> | DjangoCategory[]>(
    "/public/categories/?page_size=1000",
  );
  const rows = extractList(payload);

  const root = rows.find((c) => c.slug === categorySlug);
  if (!root) return [];

  const childrenByParent = new Map<string, string[]>();
  for (const item of rows) {
    if (item.parent == null) continue;
    const parentId = String(item.parent);
    const bucket = childrenByParent.get(parentId) ?? [];
    bucket.push(item.document_id);
    childrenByParent.set(parentId, bucket);
  }

  const visited: string[] = [];
  const queue: string[] = [root.document_id];
  while (queue.length > 0) {
    const current = queue.shift()!;
    if (visited.includes(current)) continue;
    visited.push(current);
    for (const child of childrenByParent.get(current) ?? []) {
      queue.push(child);
    }
  }

  return visited;
}

// ─── Sitemap helpers ──────────────────────────────────────────────────────────

type SitemapEntry = {
  slug: string;
  documentId?: string;
  updatedAt?: string;
};

async function getAllEntriesForSitemap(path: string): Promise<SitemapEntry[]> {
  const payload = await djangoFetch<DRFPaginatedList<Record<string, unknown>> | Record<string, unknown>[]>(path);
  const rows = extractList(payload);
  return rows.map((r) => ({
    slug: (r.slug ?? r.document_id ?? "") as string,
    documentId: (r.document_id ?? "") as string,
    updatedAt: (r.updated_at ?? r.updatedAt ?? "") as string,
  }));
}

export async function getPostsForSitemap() {
  try {
    return await getAllEntriesForSitemap("/public/posts/?ordering=-updated_at&page_size=1000");
  } catch {
    return [];
  }
}

export async function getCategoriesForSitemap() {
  try {
    return await getAllEntriesForSitemap("/public/categories/?ordering=-updated_at&page_size=1000");
  } catch {
    return [];
  }
}

export async function getTagsForSitemap() {
  try {
    return await getAllEntriesForSitemap("/public/tags/?ordering=-updated_at&page_size=1000");
  } catch {
    return [];
  }
}

export async function getPagesForSitemap() {
  try {
    return await getAllEntriesForSitemap("/public/pages/?type=footer&ordering=-updated_at&page_size=1000");
  } catch {
    return [];
  }
}
