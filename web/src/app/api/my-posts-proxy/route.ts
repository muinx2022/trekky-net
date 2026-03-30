import { NextResponse } from "next/server";

const API_URL = (process.env.STRAPI_INTERNAL_URL ?? process.env.NEXT_PUBLIC_API_URL ?? "http://127.0.0.1:8000")
  .replace("http://localhost:8000", "http://127.0.0.1:8000");
const API_BASE = `${API_URL}/api/v1`;

type PublishStatus = "published" | "draft";
type PostRow = {
  id?: number;
  documentId?: string;
  title?: string;
  slug?: string;
  excerpt?: string;
  content?: string;
  createdAt?: string;
  updatedAt?: string;
  publishedAt?: string | null;
  categories?: Array<{ id?: number; documentId?: string; name?: string; slug?: string }>;
  tags?: Array<{ id?: number; documentId?: string; name?: string; slug?: string }>;
  images?: Array<{ id?: number; url?: string; mime?: string | null; alternativeText?: string | null }>;
};
type NormalizedPost = PostRow & { status: PublishStatus };

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

async function resolveCurrentUser(authHeader: string) {
  const meRes = await fetch(`${API_BASE}/users/me`, {
    headers: { Authorization: authHeader },
    cache: "no-store",
  });
  if (!meRes.ok) {
    return { error: NextResponse.json({ error: "Unauthorized" }, { status: 401 }) };
  }
  const me = (await meRes.json()) as { id?: number };
  if (!me.id) {
    return { error: NextResponse.json({ error: "Cannot resolve current user" }, { status: 400 }) };
  }
  return { mePayload: me };
}

function sortPostsByLatest(rows: NormalizedPost[]) {
  return [...rows].sort((a, b) => {
    const aDate = new Date(a.updatedAt ?? a.publishedAt ?? a.createdAt ?? 0).getTime();
    const bDate = new Date(b.updatedAt ?? b.publishedAt ?? b.createdAt ?? 0).getTime();
    return bDate - aDate;
  });
}

async function fetchPostsByStatus(authHeader: string, status: PublishStatus) {
  const query = new URLSearchParams({ status, pageSize: "1000" });
  const res = await fetch(`${API_BASE}/posts/my-posts?${query.toString()}`, {
    headers: { Authorization: authHeader },
    cache: "no-store",
  });
  const payload = (await res.json().catch(() => ({}))) as { data?: PostRow[]; error?: { message?: string } };
  if (!res.ok) {
    return { error: NextResponse.json({ error: payload.error?.message ?? "Fetch failed" }, { status: res.status }) };
  }
  const rows = (payload.data ?? []).map((item) => ({
    ...item,
    status,
    publishedAt: status === "published" ? item.publishedAt ?? null : null,
  })) as NormalizedPost[];
  return { rows };
}

function mergePostVersions(draftRows: NormalizedPost[], publishedRows: NormalizedPost[]) {
  const merged = new Map<string, NormalizedPost>();
  for (const row of draftRows) {
    if (!row.documentId) continue;
    merged.set(row.documentId, { ...row, status: "draft", publishedAt: null });
  }
  for (const row of publishedRows) {
    if (!row.documentId) continue;
    const existing = merged.get(row.documentId);
    if (!existing) {
      merged.set(row.documentId, { ...row, status: "published", publishedAt: row.publishedAt ?? null });
    } else {
      merged.set(row.documentId, {
        ...existing,
        id: existing.id ?? row.id,
        slug: existing.slug ?? row.slug,
        categories: existing.categories ?? row.categories,
        tags: existing.tags ?? row.tags,
        status: "published",
        publishedAt: row.publishedAt ?? null,
      });
    }
  }
  return sortPostsByLatest(Array.from(merged.values()));
}

async function fetchOwnedPost(authHeader: string, documentId: string) {
  const res = await fetch(`${API_BASE}/posts/my-posts?documentId=${encodeURIComponent(documentId)}`, {
    headers: { Authorization: authHeader },
    cache: "no-store",
  });
  const payload = (await res.json().catch(() => ({}))) as { data?: PostRow | null };
  if (!res.ok || !payload.data) {
    return { error: NextResponse.json({ error: "Post not found" }, { status: 404 }) };
  }
  const post = { ...payload.data, status: payload.data.publishedAt ? "published" : "draft" } as NormalizedPost;
  return { post };
}

async function publishDocument(authHeader: string, documentId: string) {
  const tryPaths = [
    `${API_BASE}/posts/${documentId}/user-publish`,
    `${API_BASE}/posts/${documentId}/publish`,
  ];
  for (const path of tryPaths) {
    const res = await fetch(path, { method: "POST", headers: { Authorization: authHeader } });
    if (res.ok) return true;
  }
  return false;
}

async function unpublishDocument(authHeader: string, documentId: string) {
  const tryPaths = [
    `${API_BASE}/posts/${documentId}/user-unpublish`,
    `${API_BASE}/posts/${documentId}/unpublish`,
  ];
  for (const path of tryPaths) {
    const res = await fetch(path, { method: "POST", headers: { Authorization: authHeader } });
    if (res.ok) return true;
  }
  return false;
}

export async function GET(request: Request) {
  const authHeader = request.headers.get("Authorization") ?? "";
  if (!authHeader) return NextResponse.json({ error: "Unauthorized" }, { status: 401 });

  const { searchParams } = new URL(request.url);
  const page = parseInt(searchParams.get("page") || "1", 10);
  const pageSize = parseInt(searchParams.get("pageSize") || "10", 10);
  const documentId = String(searchParams.get("documentId") ?? "").trim();

  try {
    const resolved = await resolveCurrentUser(authHeader);
    if ("error" in resolved) return resolved.error;

    if (documentId) {
      const ownedPost = await fetchOwnedPost(authHeader, documentId);
      if ("error" in ownedPost) return ownedPost.error;
      return NextResponse.json({ data: ownedPost.post });
    }

    const [publishedResult, draftResult] = await Promise.all([
      fetchPostsByStatus(authHeader, "published"),
      fetchPostsByStatus(authHeader, "draft"),
    ]);

    if ("error" in publishedResult) return publishedResult.error;
    if ("error" in draftResult) return draftResult.error;

    const mergedRows = mergePostVersions(draftResult.rows, publishedResult.rows);
    const safePage = Math.max(1, page);
    const safePageSize = Math.max(1, pageSize);
    const total = mergedRows.length;
    const pageCount = Math.max(1, Math.ceil(total / safePageSize));
    const start = (safePage - 1) * safePageSize;
    const data = mergedRows.slice(start, start + safePageSize);

    return NextResponse.json({ data, meta: { pagination: { page: safePage, pageSize: safePageSize, pageCount, total } } });
  } catch {
    return NextResponse.json({ error: "Failed to fetch my posts" }, { status: 500 });
  }
}

export async function POST(request: Request) {
  const authHeader = request.headers.get("Authorization") ?? "";
  if (!authHeader) return NextResponse.json({ error: "Unauthorized" }, { status: 401 });

  const body = (await request.json().catch(() => ({}))) as {
    title?: string;
    content?: string;
    categories?: string[];
    tags?: string[];
    imageIds?: number[];
  };

  const title = String(body.title ?? "").trim();
  const content = String(body.content ?? "").trim();
  const categoryDocumentIds = Array.isArray(body.categories)
    ? body.categories.map((item) => String(item ?? "").trim()).filter(Boolean)
    : [];
  const tagDocumentIds = Array.isArray(body.tags)
    ? body.tags.map((item) => String(item ?? "").trim()).filter(Boolean)
    : [];
  const imageIds = Array.isArray(body.imageIds) ? body.imageIds.filter((id) => Number.isFinite(id)) : [];

  if (!title || !content || content === "<p></p>") {
    return NextResponse.json({ error: "Title and content are required" }, { status: 400 });
  }

  try {
    const resolved = await resolveCurrentUser(authHeader);
    if ("error" in resolved) return resolved.error;

    const baseSlug = slugify(title) || `post-${Date.now()}`;
    const slug = `${baseSlug}-${Date.now().toString().slice(-6)}`;

    // Django LegacyPostCreateView._resolve_category_documents accepts document_ids directly
    const createRes = await fetch(`${API_BASE}/posts/user-create`, {
      method: "POST",
      headers: { "Content-Type": "application/json", Authorization: authHeader },
      body: JSON.stringify({
        data: {
          title,
          slug,
          content,
          categories: categoryDocumentIds,
          tags: tagDocumentIds,
          images: imageIds,
        },
      }),
    });

    const createPayload = await createRes.json().catch(() => ({}));
    if (!createRes.ok) {
      return NextResponse.json(
        { error: (createPayload as { error?: { message?: string } })?.error?.message ?? "Create failed" },
        { status: createRes.status },
      );
    }

    return NextResponse.json(createPayload, { status: 201 });
  } catch {
    return NextResponse.json({ error: "Failed to create post" }, { status: 500 });
  }
}

export async function PUT(request: Request) {
  const authHeader = request.headers.get("Authorization") ?? "";
  if (!authHeader) return NextResponse.json({ error: "Unauthorized" }, { status: 401 });

  const body = (await request.json().catch(() => ({}))) as {
    documentId?: string;
    title?: string;
    content?: string;
    categories?: string[];
    tags?: string[];
    imageIds?: number[];
  };

  const documentId = String(body.documentId ?? "").trim();
  const title = String(body.title ?? "").trim();
  const content = String(body.content ?? "").trim();
  const categoryDocumentIds = Array.isArray(body.categories)
    ? body.categories.map((item) => String(item ?? "").trim()).filter(Boolean)
    : [];
  const tagDocumentIds = Array.isArray(body.tags)
    ? body.tags.map((item) => String(item ?? "").trim()).filter(Boolean)
    : [];
  const imageIds = Array.isArray(body.imageIds) ? body.imageIds.filter((id) => Number.isFinite(id)) : undefined;

  if (!documentId || !title || !content || content === "<p></p>") {
    return NextResponse.json({ error: "documentId, title and content are required" }, { status: 400 });
  }

  try {
    const resolved = await resolveCurrentUser(authHeader);
    if ("error" in resolved) return resolved.error;

    const updateRes = await fetch(`${API_BASE}/posts/${documentId}/user-update`, {
      method: "PUT",
      headers: { "Content-Type": "application/json", Authorization: authHeader },
      body: JSON.stringify({
        data: {
          title,
          content,
          categories: categoryDocumentIds,
          tags: tagDocumentIds,
          ...(imageIds !== undefined && { images: imageIds }),
        },
      }),
    });

    const updatePayload = await updateRes.json().catch(() => ({}));
    if (!updateRes.ok) {
      return NextResponse.json(
        { error: (updatePayload as { error?: { message?: string } })?.error?.message ?? "Update failed" },
        { status: updateRes.status },
      );
    }

    const refreshed = await fetchOwnedPost(authHeader, documentId);
    if ("error" in refreshed) return NextResponse.json(updatePayload);

    return NextResponse.json({ data: refreshed.post });
  } catch {
    return NextResponse.json({ error: "Failed to update post" }, { status: 500 });
  }
}

export async function PATCH(request: Request) {
  const authHeader = request.headers.get("Authorization") ?? "";
  if (!authHeader) return NextResponse.json({ error: "Unauthorized" }, { status: 401 });

  const body = (await request.json().catch(() => ({}))) as {
    documentId?: string;
    action?: "toggle" | "publish" | "unpublish";
    currentStatus?: PublishStatus;
  };

  const documentId = String(body.documentId ?? "").trim();
  if (!documentId) return NextResponse.json({ error: "documentId is required" }, { status: 400 });

  try {
    const resolved = await resolveCurrentUser(authHeader);
    if ("error" in resolved) return resolved.error;

    const ownedPost = await fetchOwnedPost(authHeader, documentId);
    if ("error" in ownedPost) return ownedPost.error;

    const currentStatus = body.currentStatus ?? ownedPost.post.status ?? "draft";
    const shouldPublish =
      body.action === "publish" || (body.action !== "unpublish" && currentStatus !== "published");

    const ok = shouldPublish
      ? await publishDocument(authHeader, documentId)
      : await unpublishDocument(authHeader, documentId);

    if (!ok) return NextResponse.json({ error: "Cannot change post status" }, { status: 400 });

    const refreshed = await fetchOwnedPost(authHeader, documentId);
    if ("error" in refreshed) return refreshed.error;

    return NextResponse.json({ data: refreshed.post });
  } catch {
    return NextResponse.json({ error: "Failed to toggle post status" }, { status: 500 });
  }
}
