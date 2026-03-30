import { NextRequest } from "next/server";

// Google OAuth is not configured for the Django backend
export async function GET(_req: NextRequest) {
  return Response.json({ error: "Google authentication is not available" }, { status: 501 });
}
