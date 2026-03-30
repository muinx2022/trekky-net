import { NextResponse } from "next/server";
import { nameAvatarFile } from "@/lib/media-naming";

const API_URL = (process.env.STRAPI_INTERNAL_URL ?? process.env.NEXT_PUBLIC_API_URL ?? "http://127.0.0.1:8000")
  .replace("http://localhost:8000", "http://127.0.0.1:8000");
const API_BASE = `${API_URL}/api/v1`;

type MePayload = {
  id?: number;
  username?: string;
  email?: string;
  bio?: string | null;
  avatar?: unknown;
};

async function resolveCurrentUser(authHeader: string) {
  const meRes = await fetch(`${API_BASE}/users/me`, {
    headers: { Authorization: authHeader },
    cache: "no-store",
  });

  if (!meRes.ok) {
    return { error: NextResponse.json({ error: "Unauthorized" }, { status: 401 }) };
  }

  const mePayload = (await meRes.json()) as MePayload;
  if (!mePayload.id) {
    return { error: NextResponse.json({ error: "Cannot resolve current user" }, { status: 400 }) };
  }

  return { mePayload };
}

export async function GET(request: Request) {
  const authHeader = request.headers.get("Authorization") ?? "";
  if (!authHeader) return NextResponse.json({ error: "Unauthorized" }, { status: 401 });

  try {
    const resolved = await resolveCurrentUser(authHeader);
    if ("error" in resolved) return resolved.error;
    return NextResponse.json(resolved.mePayload);
  } catch {
    return NextResponse.json({ error: "Failed to fetch profile" }, { status: 500 });
  }
}

export async function PUT(request: Request) {
  const authHeader = request.headers.get("Authorization") ?? "";
  if (!authHeader) return NextResponse.json({ error: "Unauthorized" }, { status: 401 });

  try {
    const resolved = await resolveCurrentUser(authHeader);
    if ("error" in resolved) return resolved.error;

    const formData = await request.formData();
    const bio = String(formData.get("bio") ?? "").trim();
    const avatarFile = formData.get("avatar");

    // Django LegacyMeView (PUT) accepts FormData with bio + avatar file directly
    const updateFormData = new FormData();
    updateFormData.append("bio", bio);

    if (avatarFile instanceof File && avatarFile.size > 0) {
      const renamedAvatar = nameAvatarFile(avatarFile);
      updateFormData.append("avatar", renamedAvatar, renamedAvatar.name);
    }

    const updateRes = await fetch(`${API_BASE}/me/`, {
      method: "PUT",
      headers: { Authorization: authHeader },
      body: updateFormData,
    });

    const updatePayload = await updateRes.json().catch(() => ({}));
    if (!updateRes.ok) {
      return NextResponse.json(
        { error: (updatePayload as { error?: { message?: string } })?.error?.message ?? "Update failed" },
        { status: updateRes.status },
      );
    }

    // Refresh user data
    const refreshed = await resolveCurrentUser(authHeader);
    if ("error" in refreshed) return NextResponse.json(updatePayload);

    return NextResponse.json(refreshed.mePayload);
  } catch {
    return NextResponse.json({ error: "Failed to update profile" }, { status: 500 });
  }
}
