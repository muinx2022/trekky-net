export default eventHandler(async (event) => {
  const query = getQuery(event);
  const params = new URLSearchParams();
  const targetType = typeof query.targetType === "string" ? query.targetType : "";
  const targetDocumentId = typeof query.targetDocumentId === "string" ? query.targetDocumentId : "";
  if (targetType) params.set("targetType", targetType);
  if (targetDocumentId) params.set("targetDocumentId", targetDocumentId);
  const auth = getHeader(event, "authorization") ?? "";

  try {
    const response = await fetch(`${getApiBase()}/reports/mine?${params.toString()}`, {
      headers: auth ? { Authorization: auth } : {},
      cache: "no-store",
    });
    const payload = await response.json().catch(() => ({ data: [] as Array<{ targetType?: string; targetDocumentId?: string }> }));
    setResponseStatus(event, response.status);
    const reports = Array.isArray(payload?.data) ? payload.data : [];
    const reported = !!reports.find(
      (item) =>
        (!targetType || item?.targetType === targetType) &&
        (!targetDocumentId || item?.targetDocumentId === targetDocumentId),
    );
    return { data: { reported } };
  } catch {
    return { data: { reported: false } };
  }
});
