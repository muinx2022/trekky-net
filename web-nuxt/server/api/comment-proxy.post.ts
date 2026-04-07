type DjangoComment = {
  id: number;
  document_id: string;
  target_type: string;
  target_document_id: string;
  parent?: number | null;
  author?: { id: number; username: string; avatar?: string | null } | null;
  author_name?: string;
  content: string;
  created_at?: string;
};

function toAbsoluteUrl(url?: string | null) {
  if (!url) return null;
  return url.startsWith("http://") || url.startsWith("https://") ? url : `${getDjangoUrl()}${url}`;
}

function normalizeComment(raw: DjangoComment, parentDocumentId?: string) {
  return {
    id: raw.id,
    documentId: raw.document_id,
    authorName: raw.author?.username ?? raw.author_name ?? "Anonymous",
    authorAvatarUrl: raw.author?.avatar ? toAbsoluteUrl(raw.author.avatar) : null,
    content: raw.content,
    targetType: raw.target_type,
    targetDocumentId: raw.target_document_id,
    createdAt: raw.created_at ?? new Date().toISOString(),
    parent: parentDocumentId ? { documentId: parentDocumentId } : null,
  };
}

async function resolveParentId(parentDocumentId: string, authHeader: string) {
  const response = await fetch(`${getApiBase()}/public/comments/${encodeURIComponent(parentDocumentId)}/`, {
    headers: authHeader ? { Authorization: authHeader } : {},
    cache: "no-store",
  });
  if (!response.ok) return null;
  const data = (await response.json()) as { id?: number };
  return data.id ?? null;
}

export default eventHandler(async (event) => {
  const auth = getHeader(event, "authorization") ?? "";
  if (!auth) throw createError({ statusCode: 401, statusMessage: "Login required to post a comment" });
  const body = await readBody<Record<string, string>>(event);
  const targetType = body.targetType ?? body.target_type ?? "";
  const targetDocumentId = body.targetDocumentId ?? body.target_document_id ?? "";
  const content = body.content ?? "";
  const parentDocumentId = body.parent ?? undefined;

  const payload: Record<string, unknown> = {
    target_type: targetType,
    target_document_id: targetDocumentId,
    content,
  };

  if (parentDocumentId) {
    const parentPk = await resolveParentId(parentDocumentId, auth);
    if (parentPk != null) payload.parent = parentPk;
  }

  const response = await fetch(`${getApiBase()}/public/comments/`, {
    method: "POST",
    headers: { "Content-Type": "application/json", Authorization: auth },
    body: JSON.stringify(payload),
  });
  const raw = await response.json().catch(() => ({}));
  if (!response.ok) {
    throw createError({ statusCode: response.status, statusMessage: raw?.detail || raw?.error?.message || "Comment failed" });
  }
  return { data: normalizeComment(raw as DjangoComment, parentDocumentId) };
});
