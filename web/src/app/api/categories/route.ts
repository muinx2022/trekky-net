import { NextResponse } from "next/server";

const API_URL = (process.env.STRAPI_INTERNAL_URL ?? process.env.NEXT_PUBLIC_API_URL ?? "http://127.0.0.1:8000")
  .replace("http://localhost:8000", "http://127.0.0.1:8000");
const API_BASE = `${API_URL}/api/v1`;

export async function GET() {
  try {
    const res = await fetch(`${API_BASE}/public/categories/?page_size=1000`, {
      headers: { "Content-Type": "application/json" },
      cache: "no-store",
    });
    if (!res.ok) {
      return NextResponse.json({ data: [], error: `Upstream returned ${res.status}` }, { status: res.status });
    }
    const payload = await res.json().catch(() => []);
    return NextResponse.json(payload);
  } catch {
    return NextResponse.json({ data: [], error: "Cannot connect to categories API" }, { status: 502 });
  }
}
