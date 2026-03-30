import { NextResponse } from "next/server";

const API_URL = (process.env.STRAPI_INTERNAL_URL ?? process.env.NEXT_PUBLIC_API_URL ?? "http://127.0.0.1:8000")
  .replace("http://localhost:8000", "http://127.0.0.1:8000");
const API_BASE = `${API_URL}/api/v1`;

type DjangoInteraction = {
  id: number;
  target_type: string;
  target_document_id: string;
  action_type: string;
  created_at?: string;
};

function extractList<T>(payload: { count?: number; results?: T[] } | T[]): T[] {
  if (Array.isArray(payload)) return payload;
  return payload.results ?? [];
}

async function getUserInteractions(authHeader: string): Promise<DjangoInteraction[]> {
  const res = await fetch(`${API_BASE}/public/interactions/`, {
    headers: { Authorization: authHeader },
    cache: "no-store",
  });
  if (!res.ok) return [];
  const data = await res.json();
  return extractList<DjangoInteraction>(data);
}

// Toggle: check if interaction exists, then create or delete
export async function POST(request: Request) {
  const authHeader = request.headers.get("Authorization") ?? "";
  if (!authHeader) {
    return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
  }

  const body = await request.json();
  const actionType = body.actionType ?? body.action_type ?? "like";
  const targetType = body.targetType ?? body.target_type ?? "";
  const targetDocumentId = body.targetDocumentId ?? body.target_document_id ?? "";

  if (!targetType || !targetDocumentId) {
    return NextResponse.json({ error: "targetType and targetDocumentId are required" }, { status: 400 });
  }

  try {
    const interactions = await getUserInteractions(authHeader);
    const existing = interactions.find(
      (i) =>
        i.action_type === actionType &&
        i.target_type === targetType &&
        i.target_document_id === targetDocumentId,
    );

    if (existing) {
      const deleteRes = await fetch(`${API_BASE}/public/interactions/${existing.id}/`, {
        method: "DELETE",
        headers: { Authorization: authHeader },
      });
      if (!deleteRes.ok && deleteRes.status !== 204) {
        return NextResponse.json({ error: "Failed to remove interaction" }, { status: deleteRes.status });
      }
      return NextResponse.json({ toggled: false, actionType });
    } else {
      const createRes = await fetch(`${API_BASE}/public/interactions/`, {
        method: "POST",
        headers: { "Content-Type": "application/json", Authorization: authHeader },
        body: JSON.stringify({
          target_type: targetType,
          target_document_id: targetDocumentId,
          action_type: actionType,
        }),
      });
      const createData = await createRes.json().catch(() => ({}));
      if (!createRes.ok) {
        return NextResponse.json({ error: "Failed to create interaction" }, { status: createRes.status });
      }
      return NextResponse.json({ toggled: true, actionType, data: createData });
    }
  } catch {
    return NextResponse.json({ error: "Cannot connect to API" }, { status: 502 });
  }
}

// GET: fetch interaction state for a specific target (requires auth)
export async function GET(request: Request) {
  const { searchParams } = new URL(request.url);
  const targetType = searchParams.get("targetType") ?? "";
  const targetDocumentId = searchParams.get("targetDocumentId") ?? "";
  const authHeader = request.headers.get("Authorization") ?? "";

  if (!authHeader || !targetType) {
    return NextResponse.json({ liked: false, followed: false, likesCount: 0, followsCount: 0 });
  }

  try {
    const interactions = await getUserInteractions(authHeader);

    const relevant = targetDocumentId
      ? interactions.filter(
          (i) => i.target_type === targetType && i.target_document_id === targetDocumentId,
        )
      : interactions.filter((i) => i.target_type === targetType);

    if (!targetDocumentId) {
      return NextResponse.json({
        data: relevant.map((i) => ({ actionType: i.action_type, targetDocumentId: i.target_document_id })),
        likesCount: 0,
        followsCount: 0,
      });
    }

    return NextResponse.json({
      liked: relevant.some((i) => i.action_type === "like"),
      followed: relevant.some((i) => i.action_type === "follow"),
      likesCount: 0,
      followsCount: 0,
    });
  } catch {
    return NextResponse.json({ liked: false, followed: false, likesCount: 0, followsCount: 0 });
  }
}
