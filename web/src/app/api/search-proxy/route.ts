import { NextResponse } from "next/server";

const API_URL = (process.env.STRAPI_INTERNAL_URL ?? process.env.NEXT_PUBLIC_API_URL ?? "http://127.0.0.1:8000")
  .replace("http://localhost:8000", "http://127.0.0.1:8000");
const API_BASE = `${API_URL}/api/v1`;

function normalizeDjangoDoc(doc: Record<string, unknown>) {
  return { ...doc, documentId: doc.document_id ?? doc.documentId };
}

export async function GET(request: Request) {
  const { searchParams } = new URL(request.url);
  const q = searchParams.get("q") || "";

  if (!q.trim()) {
    return NextResponse.json({ posts: [], tags: [], categories: [] });
  }

  try {
    const res = await fetch(`${API_BASE}/public/search/?q=${encodeURIComponent(q)}`, { cache: "no-store" });
    if (!res.ok) {
      return NextResponse.json({ posts: [], tags: [], categories: [] });
    }
    const data = (await res.json()) as { posts?: unknown[]; tags?: unknown[]; categories?: unknown[] };
    return NextResponse.json({
      posts: (data.posts ?? []).map((d) => normalizeDjangoDoc(d as Record<string, unknown>)),
      tags: (data.tags ?? []).map((d) => normalizeDjangoDoc(d as Record<string, unknown>)),
      categories: (data.categories ?? []).map((d) => normalizeDjangoDoc(d as Record<string, unknown>)),
    });
  } catch (error) {
    console.error("Search error:", error);
    return NextResponse.json({ error: "Search failed" }, { status: 500 });
  }
}
