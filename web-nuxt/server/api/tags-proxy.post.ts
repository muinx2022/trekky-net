export default eventHandler(async (event) => {
  const auth = getHeader(event, "authorization") ?? "";
  if (!auth) throw createError({ statusCode: 401, statusMessage: "Unauthorized" });
  const body = await readBody<{ name?: string }>(event);
  const name = String(body?.name ?? "").trim();
  if (!name) throw createError({ statusCode: 400, statusMessage: "Tag name is required" });

  const response = await fetch(`${getApiBase()}/tags/user-create`, {
    method: "POST",
    headers: { "Content-Type": "application/json", Authorization: auth },
    body: JSON.stringify({ name }),
  });
  const payload = await response.json().catch(() => ({}));
  setResponseStatus(event, response.status);
  return payload;
});
