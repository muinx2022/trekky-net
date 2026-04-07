type DjangoInteraction = {
  id: number;
  target_type: string;
  target_document_id: string;
  action_type: string;
};

function extractList<T>(payload: { results?: T[] } | T[]) {
  return Array.isArray(payload) ? payload : payload.results ?? [];
}

async function getUserInteractions(authHeader: string) {
  const response = await fetch(`${getApiBase()}/public/interactions/`, {
    headers: { Authorization: authHeader },
    cache: "no-store",
  });
  if (!response.ok) return [];
  return extractList<DjangoInteraction>(await response.json());
}

export default eventHandler(async (event) => {
  const auth = getHeader(event, "authorization") ?? "";
  if (!auth) throw createError({ statusCode: 401, statusMessage: "Unauthorized" });
  const body = await readBody<Record<string, string>>(event);
  const actionType = body.actionType ?? body.action_type ?? "like";
  const targetType = body.targetType ?? body.target_type ?? "";
  const targetDocumentId = body.targetDocumentId ?? body.target_document_id ?? "";
  if (!targetType || !targetDocumentId) {
    throw createError({ statusCode: 400, statusMessage: "targetType and targetDocumentId are required" });
  }
  const interactions = await getUserInteractions(auth);
  const existing = interactions.find(
    (item) =>
      item.action_type === actionType &&
      item.target_type === targetType &&
      item.target_document_id === targetDocumentId,
  );
  if (existing) {
    const deleteResponse = await fetch(`${getApiBase()}/public/interactions/${existing.id}/`, {
      method: "DELETE",
      headers: { Authorization: auth },
    });
    if (!deleteResponse.ok && deleteResponse.status !== 204) {
      throw createError({ statusCode: deleteResponse.status, statusMessage: "Failed to remove interaction" });
    }
    return { toggled: false, actionType };
  }
  const createResponse = await fetch(`${getApiBase()}/public/interactions/`, {
    method: "POST",
    headers: { "Content-Type": "application/json", Authorization: auth },
    body: JSON.stringify({
      target_type: targetType,
      target_document_id: targetDocumentId,
      action_type: actionType,
    }),
  });
  const payload = await createResponse.json().catch(() => ({}));
  if (!createResponse.ok) throw createError({ statusCode: createResponse.status, statusMessage: "Failed to create interaction" });
  return { toggled: true, actionType, data: payload };
});
