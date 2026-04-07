type PublishStatus = "published" | "draft";

async function fetchOwnedPost(authHeader: string, documentId: string) {
  const response = await fetch(`${getApiBase()}/posts/my-posts?documentId=${encodeURIComponent(documentId)}`, {
    headers: { Authorization: authHeader },
    cache: "no-store",
  });
  const payload = (await response.json().catch(() => ({}))) as { data?: { status?: PublishStatus } | null };
  if (!response.ok || !payload.data) throw createError({ statusCode: 404, statusMessage: "Post not found" });
  return payload.data;
}

async function publishDocument(authHeader: string, documentId: string) {
  for (const path of [`${getApiBase()}/posts/${documentId}/user-publish`, `${getApiBase()}/posts/${documentId}/publish`]) {
    const response = await fetch(path, { method: "POST", headers: { Authorization: authHeader } });
    if (response.ok) return true;
  }
  return false;
}

async function unpublishDocument(authHeader: string, documentId: string) {
  for (const path of [`${getApiBase()}/posts/${documentId}/user-unpublish`, `${getApiBase()}/posts/${documentId}/unpublish`]) {
    const response = await fetch(path, { method: "POST", headers: { Authorization: authHeader } });
    if (response.ok) return true;
  }
  return false;
}

export default eventHandler(async (event) => {
  const auth = getHeader(event, "authorization") ?? "";
  if (!auth) throw createError({ statusCode: 401, statusMessage: "Unauthorized" });
  const body = await readBody<{ documentId?: string; action?: "toggle" | "publish" | "unpublish"; currentStatus?: PublishStatus }>(event);
  const documentId = String(body?.documentId ?? "").trim();
  if (!documentId) throw createError({ statusCode: 400, statusMessage: "documentId is required" });
  const post = await fetchOwnedPost(auth, documentId);
  const currentStatus = body?.currentStatus ?? post.status ?? "draft";
  const shouldPublish = body?.action === "publish" || (body?.action !== "unpublish" && currentStatus !== "published");
  const ok = shouldPublish ? await publishDocument(auth, documentId) : await unpublishDocument(auth, documentId);
  if (!ok) throw createError({ statusCode: 400, statusMessage: "Cannot change post status" });
  return { data: await fetchOwnedPost(auth, documentId) };
});
