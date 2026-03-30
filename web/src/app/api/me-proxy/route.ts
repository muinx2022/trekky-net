import { NextRequest } from "next/server";

const DJANGO_URL = (
  process.env.STRAPI_INTERNAL_URL ??
  process.env.NEXT_PUBLIC_API_URL ??
  "http://127.0.0.1:8000"
).replace("http://localhost:8000", "http://127.0.0.1:8000");

export async function GET(req: NextRequest) {
  const auth = req.headers.get("Authorization");
  if (!auth) return Response.json({ error: "Unauthorized" }, { status: 401 });

  const res = await fetch(`${DJANGO_URL}/api/v1/users/me`, {
    headers: { Authorization: auth },
    cache: "no-store",
  });

  const data = await res.json();
  return Response.json(data, { status: res.status });
}
