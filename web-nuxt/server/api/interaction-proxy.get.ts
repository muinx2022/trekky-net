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
  const query = getQuery(event);
  const targetType = typeof query.targetType === "string" ? query.targetType : "";
  const targetDocumentId = typeof query.targetDocumentId === "string" ? query.targetDocumentId : "";
  const auth = getHeader(event, "authorization") ?? "";
  if (!auth || !targetType) return { liked: false, followed: false, likesCount: 0, followsCount: 0 };
  const interactions = await getUserInteractions(auth);
  const relevant = targetDocumentId
    ? interactions.filter((item) => item.target_type === targetType && item.target_document_id === targetDocumentId)
    : interactions.filter((item) => item.target_type === targetType);
  if (!targetDocumentId) {
    return {
      data: relevant.map((item) => ({ actionType: item.action_type, targetDocumentId: item.target_document_id })),
      likesCount: 0,
      followsCount: 0,
    };
  }
  return {
    liked: relevant.some((item) => item.action_type === "like"),
    followed: relevant.some((item) => item.action_type === "follow"),
    likesCount: 0,
    followsCount: 0,
  };
});
