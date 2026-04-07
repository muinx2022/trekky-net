const normalizeDoc = (doc: Record<string, unknown>) => ({ ...doc, documentId: doc.document_id ?? doc.documentId });

export default eventHandler(async (event) => {
  const query = getQuery(event);
  const q = typeof query.q === "string" ? query.q : "";
  if (!q.trim()) return { posts: [], tags: [], categories: [] };

  try {
    const response = await fetch(`${getApiBase()}/public/search/?q=${encodeURIComponent(q)}`, { cache: "no-store" });
    if (!response.ok) return { posts: [], tags: [], categories: [] };
    const data = (await response.json()) as { posts?: unknown[]; tags?: unknown[]; categories?: unknown[] };
    return {
      posts: (data.posts ?? []).map((item) => normalizeDoc(item as Record<string, unknown>)),
      tags: (data.tags ?? []).map((item) => normalizeDoc(item as Record<string, unknown>)),
      categories: (data.categories ?? []).map((item) => normalizeDoc(item as Record<string, unknown>)),
    };
  } catch {
    throw createError({ statusCode: 500, statusMessage: "Search failed" });
  }
});
