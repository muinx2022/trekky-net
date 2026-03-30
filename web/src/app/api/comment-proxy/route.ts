import { NextResponse } from "next/server";

const API_URL = (process.env.STRAPI_INTERNAL_URL ?? process.env.NEXT_PUBLIC_API_URL ?? "http://127.0.0.1:8000")
  .replace("http://localhost:8000", "http://127.0.0.1:8000");
const API_BASE = `${API_URL}/api/v1`;

type DjangoComment = {
  id: number;
  document_id: string;
  target_type: string;
  target_document_id: string;
  parent?: number | null;
  author?: { id: number; username: string; avatar?: string | null } | null;
  author_name?: string;
  content: string;
  status?: string;
  created_at?: string;
};

function toAbsoluteUrl(url?: string | null): string | null {
  if (!url) return null;
  if (url.startsWith("http://") || url.startsWith("https://")) return url;
  return `${API_URL}${url}`;
}

function normalizeDjangoComment(raw: DjangoComment, parentDocumentId?: string) {
  return {
    id: raw.id,
    documentId: raw.document_id,
    authorName: raw.author?.username ?? raw.author_name ?? "Anonymous",
    authorAvatarUrl: raw.author?.avatar ? toAbsoluteUrl(raw.author.avatar) : null,
    content: raw.content,
    targetType: raw.target_type,
    targetDocumentId: raw.target_document_id,
    createdAt: raw.created_at ?? new Date().toISOString(),
    parent: parentDocumentId ? { documentId: parentDocumentId } : null,
  };
}

async function resolveParentId(parentDocumentId: string, authHeader: string): Promise<number | null> {
  try {
    const res = await fetch(
      `${API_BASE}/public/comments/${encodeURIComponent(parentDocumentId)}/`,
      { headers: authHeader ? { Authorization: authHeader } : {}, cache: "no-store" },
    );
    if (!res.ok) return null;
    const data = (await res.json()) as { id?: number };
    return data.id ?? null;
  } catch {
    return null;
  }
}

export async function POST(request: Request) {
  const authHeader = request.headers.get("Authorization") ?? "";
  if (!authHeader) {
    return NextResponse.json({ error: "Login required to post a comment" }, { status: 401 });
  }

  const body = await request.json();
  const targetType = body.targetType ?? body.target_type ?? "";
  const targetDocumentId = body.targetDocumentId ?? body.target_document_id ?? "";
  const content = body.content ?? "";
  const parentDocumentId: string | undefined = body.parent ?? undefined;

  const djangoBody: Record<string, unknown> = {
    target_type: targetType,
    target_document_id: targetDocumentId,
    content,
  };

  // Resolve parent document_id → integer PK
  if (parentDocumentId) {
    const parentPk = await resolveParentId(parentDocumentId, authHeader);
    if (parentPk != null) {
      djangoBody.parent = parentPk;
    }
  }

  let res: Response;
  try {
    res = await fetch(`${API_BASE}/public/comments/`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: authHeader,
      },
      body: JSON.stringify(djangoBody),
    });
  } catch {
    return NextResponse.json({ error: "Cannot connect to API" }, { status: 502 });
  }

  const raw = await res.json().catch(() => ({}));

  if (!res.ok) {
    const detail = (raw as { detail?: string })?.detail ?? "";
    const isTokenInvalid = res.status === 401 || detail.toLowerCase().includes("token");
    const msg = isTokenInvalid
      ? "Phiên đăng nhập đã hết hạn. Vui lòng đăng nhập lại."
      : detail || (raw as { error?: { message?: string } })?.error?.message || "Gửi bình luận thất bại.";
    return NextResponse.json({ error: msg, tokenExpired: isTokenInvalid }, { status: res.status });
  }

  // Normalize to match frontend Comment type and wrap in { data: ... }
  const normalized = normalizeDjangoComment(raw as DjangoComment, parentDocumentId);
  return NextResponse.json({ data: normalized }, { status: res.status });
}
