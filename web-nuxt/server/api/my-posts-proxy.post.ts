function slugify(input: string) {
  return input
    .replace(/[đĐ]/g, "d")
    .toLowerCase()
    .trim()
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "")
    .replace(/[^a-z0-9\s-]/g, "")
    .replace(/\s+/g, "-")
    .replace(/-+/g, "-")
    .replace(/^-|-$/g, "");
}

export default eventHandler(async (event) => {
  const auth = getHeader(event, "authorization") ?? "";
  if (!auth) throw createError({ statusCode: 401, statusMessage: "Unauthorized" });
  const body = await readBody<{
    title?: string;
    content?: string;
    categories?: string[];
    tags?: string[];
    imageIds?: number[];
  }>(event);
  const title = String(body?.title ?? "").trim();
  const content = String(body?.content ?? "").trim();
  const categories = Array.isArray(body?.categories) ? body.categories.map((item) => String(item).trim()).filter(Boolean) : [];
  const tags = Array.isArray(body?.tags) ? body.tags.map((item) => String(item).trim()).filter(Boolean) : [];
  const imageIds = Array.isArray(body?.imageIds) ? body.imageIds.filter((id) => Number.isFinite(id)) : [];
  if (!title || !content || content === "<p></p>") {
    throw createError({ statusCode: 400, statusMessage: "Title and content are required" });
  }
  const slug = `${slugify(title) || `post-${Date.now()}`}-${Date.now().toString().slice(-6)}`;
  const response = await fetch(`${getApiBase()}/posts/user-create`, {
    method: "POST",
    headers: { "Content-Type": "application/json", Authorization: auth },
    body: JSON.stringify({ data: { title, slug, content, categories, tags, images: imageIds } }),
  });
  const payload = await response.json().catch(() => ({}));
  setResponseStatus(event, response.status);
  return payload;
});
