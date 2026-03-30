import { NextResponse } from "next/server";

const API_URL = (process.env.STRAPI_INTERNAL_URL ?? process.env.NEXT_PUBLIC_API_URL ?? "http://127.0.0.1:8000")
  .replace("http://localhost:8000", "http://127.0.0.1:8000");
const API_BASE = `${API_URL}/api/v1`;

export async function GET(request: Request) {
  const { searchParams } = new URL(request.url);
  const q = (searchParams.get("q") ?? "").trim().toLowerCase();

  try {
    const res = await fetch(`${API_BASE}/public/tags/?page_size=1000`, {
      headers: { "Content-Type": "application/json" },
      cache: "no-store",
    });
    if (!res.ok) {
      return NextResponse.json({ data: [] }, { status: res.status });
    }

    const payload = (await res.json().catch(() => [])) as Array<{ document_id?: string; name?: string }> | { results?: Array<{ document_id?: string; name?: string }> };
    const rows = Array.isArray(payload) ? payload : (payload.results ?? []);
    const data = rows
      .filter((row) => row.document_id && row.name)
      .filter((row) => !q || row.name!.toLowerCase().includes(q))
      .slice(0, 8)
      .map((row) => ({ documentId: row.document_id!, name: row.name! }));

    return NextResponse.json({ data });
  } catch {
    return NextResponse.json({ data: [], error: "Cannot load tags" }, { status: 502 });
  }
}

export async function POST(request: Request) {
  const authHeader = request.headers.get("Authorization") ?? "";
  if (!authHeader) {
    return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
  }

  const body = (await request.json().catch(() => ({}))) as { name?: string };
  const name = String(body.name ?? "").trim();
  if (!name) {
    return NextResponse.json({ error: "Tag name is required" }, { status: 400 });
  }

  const res = await fetch(`${API_BASE}/tags/user-create`, {
    method: "POST",
    headers: { "Content-Type": "application/json", Authorization: authHeader },
    body: JSON.stringify({ name }),
  });

  const payload = await res.json().catch(() => ({}));
  return NextResponse.json(payload, { status: res.status });
}
