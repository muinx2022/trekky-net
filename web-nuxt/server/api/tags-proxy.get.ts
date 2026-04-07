export default eventHandler(async (event) => {
  const query = getQuery(event);
  const q = typeof query.q === "string" ? query.q.trim().toLowerCase() : "";
  const response = await fetch(`${getApiBase()}/public/tags/?page_size=1000`, {
    headers: { "Content-Type": "application/json" },
    cache: "no-store",
  });
  const payload = (await response.json().catch(() => ({ results: [] }))) as
    | Array<{ document_id?: string; name?: string; slug?: string; description?: string }>
    | { results?: Array<{ document_id?: string; name?: string; slug?: string; description?: string }> };
  const rows = Array.isArray(payload) ? payload : payload.results ?? [];
  return {
    data: rows
      .filter((row) => row.document_id && row.name && row.slug)
      .filter((row) => !q || row.name!.toLowerCase().includes(q))
      .slice(0, 8)
      .map((row) => ({
        id: 0,
        documentId: row.document_id!,
        name: row.name!,
        slug: row.slug!,
        description: row.description,
      })),
  };
});
