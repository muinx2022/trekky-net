type PublishStatus = "published" | "draft";
type PostRow = {
  id?: number;
  documentId?: string;
  title?: string;
  slug?: string;
  excerpt?: string;
  content?: string;
  createdAt?: string;
  updatedAt?: string;
  publishedAt?: string | null;
  categories?: Array<{ id?: number; documentId?: string; name?: string; slug?: string }>;
  tags?: Array<{ id?: number; documentId?: string; name?: string; slug?: string }>;
  images?: Array<{ id?: number; url?: string; mime?: string | null; alternativeText?: string | null }>;
};
type NormalizedPost = PostRow & { status: PublishStatus };

async function resolveCurrentUser(authHeader: string) {
  const response = await fetch(`${getApiBase()}/users/me`, {
    headers: { Authorization: authHeader },
    cache: "no-store",
  });
  if (!response.ok) throw createError({ statusCode: 401, statusMessage: "Unauthorized" });
}

function sortPostsByLatest(rows: NormalizedPost[]) {
  return [...rows].sort((a, b) => {
    const aDate = new Date(a.updatedAt ?? a.publishedAt ?? a.createdAt ?? 0).getTime();
    const bDate = new Date(b.updatedAt ?? b.publishedAt ?? b.createdAt ?? 0).getTime();
    return bDate - aDate;
  });
}

async function fetchPostsByStatus(authHeader: string, status: PublishStatus) {
  const query = new URLSearchParams({ status, pageSize: "1000" });
  const response = await fetch(`${getApiBase()}/posts/my-posts?${query.toString()}`, {
    headers: { Authorization: authHeader },
    cache: "no-store",
  });
  const payload = (await response.json().catch(() => ({}))) as { data?: PostRow[]; error?: { message?: string } };
  if (!response.ok) throw createError({ statusCode: response.status, statusMessage: payload.error?.message || "Fetch failed" });
  return (payload.data ?? []).map((item) => ({ ...item, status, publishedAt: status === "published" ? item.publishedAt ?? null : null })) as NormalizedPost[];
}

function mergePostVersions(draftRows: NormalizedPost[], publishedRows: NormalizedPost[]) {
  const merged = new Map<string, NormalizedPost>();
  draftRows.forEach((row) => {
    if (row.documentId) merged.set(row.documentId, { ...row, status: "draft", publishedAt: null });
  });
  publishedRows.forEach((row) => {
    if (!row.documentId) return;
    const existing = merged.get(row.documentId);
    if (!existing) merged.set(row.documentId, { ...row, status: "published", publishedAt: row.publishedAt ?? null });
    else {
      merged.set(row.documentId, {
        ...existing,
        id: existing.id ?? row.id,
        slug: existing.slug ?? row.slug,
        categories: existing.categories ?? row.categories,
        tags: existing.tags ?? row.tags,
        status: "published",
        publishedAt: row.publishedAt ?? null,
      });
    }
  });
  return sortPostsByLatest(Array.from(merged.values()));
}

async function fetchOwnedPost(authHeader: string, documentId: string) {
  const response = await fetch(`${getApiBase()}/posts/my-posts?documentId=${encodeURIComponent(documentId)}`, {
    headers: { Authorization: authHeader },
    cache: "no-store",
  });
  const payload = (await response.json().catch(() => ({}))) as { data?: PostRow | null };
  if (!response.ok || !payload.data) throw createError({ statusCode: 404, statusMessage: "Post not found" });
  return { ...payload.data, status: payload.data.publishedAt ? "published" : "draft" } as NormalizedPost;
}

export default eventHandler(async (event) => {
  const auth = getHeader(event, "authorization") ?? "";
  if (!auth) throw createError({ statusCode: 401, statusMessage: "Unauthorized" });
  await resolveCurrentUser(auth);

  const query = getQuery(event);
  const page = Number(query.page ?? 1);
  const pageSize = Number(query.pageSize ?? 10);
  const documentId = typeof query.documentId === "string" ? query.documentId.trim() : "";

  if (documentId) return { data: await fetchOwnedPost(auth, documentId) };

  const [publishedRows, draftRows] = await Promise.all([fetchPostsByStatus(auth, "published"), fetchPostsByStatus(auth, "draft")]);
  const mergedRows = mergePostVersions(draftRows, publishedRows);
  const safePage = Math.max(1, page || 1);
  const safePageSize = Math.max(1, pageSize || 10);
  const total = mergedRows.length;
  const pageCount = Math.max(1, Math.ceil(total / safePageSize));
  const start = (safePage - 1) * safePageSize;
  return {
    data: mergedRows.slice(start, start + safePageSize),
    meta: { pagination: { page: safePage, pageSize: safePageSize, pageCount, total } },
  };
});
