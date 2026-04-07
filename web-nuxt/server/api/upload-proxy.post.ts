export default eventHandler(async (event) => {
  const auth = getHeader(event, "authorization") ?? "";
  if (!auth) throw createError({ statusCode: 401, statusMessage: "Unauthorized" });

  const incoming = await readFormData(event);
  const formData = new FormData();
  for (const [key, value] of incoming.entries()) {
    if (value instanceof File) formData.append(key, value, value.name);
    else formData.append(key, String(value));
  }

  const response = await fetch(`${getApiBase()}/upload`, {
    method: "POST",
    headers: { Authorization: auth },
    body: formData,
  });
  const payload = await response.json().catch(() => ([]));
  setResponseStatus(event, response.status);
  return payload;
});
