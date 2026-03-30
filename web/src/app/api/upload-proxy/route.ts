import { NextResponse } from "next/server";

const API_URL = (process.env.STRAPI_INTERNAL_URL ?? process.env.NEXT_PUBLIC_API_URL ?? "http://127.0.0.1:8000")
  .replace("http://localhost:8000", "http://127.0.0.1:8000");
const API_BASE = `${API_URL}/api/v1`;

export async function POST(request: Request) {
  const authHeader = request.headers.get("Authorization") ?? "";
  if (!authHeader) {
    return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
  }

  try {
    const incoming = await request.formData();
    const formData = new FormData();
    for (const [key, value] of incoming.entries()) {
      if (value instanceof File) {
        formData.append(key, value, value.name);
      } else {
        formData.append(key, value);
      }
    }

    const uploadRes = await fetch(`${API_BASE}/upload`, {
      method: "POST",
      headers: { Authorization: authHeader },
      body: formData,
    });

    const payload = await uploadRes.json().catch(() => ([]));

    if (!uploadRes.ok) {
      const message = Array.isArray(payload)
        ? "Upload failed"
        : (payload as { error?: { message?: string }; message?: string })?.error?.message ||
          (payload as { message?: string })?.message ||
          "Upload failed";
      return NextResponse.json({ error: message }, { status: uploadRes.status });
    }

    return NextResponse.json(payload);
  } catch (err) {
    console.error("[upload-proxy] Error:", err);
    return NextResponse.json({ error: "Upload failed" }, { status: 500 });
  }
}
