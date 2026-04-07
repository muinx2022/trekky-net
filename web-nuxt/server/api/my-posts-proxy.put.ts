async function fetchOwnedPost(authHeader: string, documentId: string) {
  const response = await fetch(`${getApiBase()}/posts/my-posts?documentId=${encodeURIComponent(documentId)}`, {
    headers: { Authorization: authHeader },
    cache: "no-store",
  });
  const payload = (await response.json().catch(() => ({}))) as { data?: unknown };
  return payload.data ?? null;
}

export default eventHandler(async (event) => {
  const auth = getHeader(event, "authorization") ?? "";
  if (!auth) throw createError({ statusCode: 401, statusMessage: "Unauthorized" });
  const body = await readBody<{
    documentId?: string;
    title?: string;
    content?: string;
    categories?: string[];
    tags?: string[];
    imageIds?: number[];
  }>(event);
  const documentId = String(body?.documentId ?? "").trim();
  const title = String(body?.title ?? "").trim();
  const content = String(body?.content ?? "").trim();
  const categories = Array.isArray(body?.categories) ? body.categories.map((item) => String(item).trim()).filter(Boolean) : [];
  const tags = Array.isArray(body?.tags) ? body.tags.map((item) => String(item).trim()).filter(Boolean) : [];
  const imageIds = Array.isArray(body?.imageIds) ? body.imageIds.filter((id) => Number.isFinite(id)) : undefined;
  if (!documentId || !title || !content || content === "<p></p>") {
    throw createError({ statusCode: 400, statusMessage: "documentId, title and content are required" });
  }
  const response = await fetch(`${getApiBase()}/posts/${documentId}/user-update`, {
    method: "PUT",
    headers: { "Content-Type": "application/json", Authorization: auth },
    body: JSON.stringify({
      data: {
        title,
        content,
        categories,
        tags,
        ...(imageIds !== undefined && { images: imageIds }),
      },
    }),
  });
  const payload = await response.json().catch(() => ({}));
  if (!response.ok) {
    throw createError({ statusCode: response.status, statusMessage: payload?.error?.message || "Update failed" });
  }
  return { data: await fetchOwnedPost(auth, documentId) ?? payload };
});
