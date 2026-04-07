export default eventHandler(async (event) => {
  try {
    const response = await fetch(`${getApiBase()}/public/categories/?page_size=1000`, {
      headers: { "Content-Type": "application/json" },
      cache: "no-store",
    });
    const payload = await response.json().catch(() => ({ results: [] }));
    setResponseStatus(event, response.status);
    return payload;
  } catch {
    throw createError({ statusCode: 502, statusMessage: "Cannot connect to categories API" });
  }
});
