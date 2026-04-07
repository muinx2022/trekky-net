export default eventHandler(async (event) => {
  const auth = getHeader(event, "authorization");
  if (!auth) throw createError({ statusCode: 401, statusMessage: "Unauthorized" });

  const response = await fetch(`${getApiBase()}/users/me`, {
    headers: { Authorization: auth },
    cache: "no-store",
  });
  setResponseStatus(event, response.status);
  return response.json();
});
