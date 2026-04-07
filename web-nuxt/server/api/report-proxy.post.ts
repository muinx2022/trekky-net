export default eventHandler(async (event) => {
  const auth = getHeader(event, "authorization") ?? "";
  const body = await readBody(event);
  const response = await fetch(`${getApiBase()}/reports/submit`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      ...(auth ? { Authorization: auth } : {}),
    },
    body: JSON.stringify(body),
  });
  const payload = await response.json().catch(() => ({}));
  setResponseStatus(event, response.status);
  return payload;
});
