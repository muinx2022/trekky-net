import { nameAvatarFile } from "../../shared/media-naming";

type MePayload = { id?: number };

async function resolveCurrentUser(authHeader: string) {
  const response = await fetch(`${getApiBase()}/users/me`, {
    headers: { Authorization: authHeader },
    cache: "no-store",
  });
  if (!response.ok) throw createError({ statusCode: 401, statusMessage: "Unauthorized" });
  const payload = (await response.json()) as MePayload;
  if (!payload.id) throw createError({ statusCode: 400, statusMessage: "Cannot resolve current user" });
}

export default eventHandler(async (event) => {
  const auth = getHeader(event, "authorization");
  if (!auth) throw createError({ statusCode: 401, statusMessage: "Unauthorized" });

  await resolveCurrentUser(auth);
  const incoming = await readFormData(event);
  const formData = new FormData();
  formData.append("bio", String(incoming.get("bio") ?? "").trim());
  const removeAvatar = String(incoming.get("removeAvatar") ?? "").toLowerCase() === "true";
  if (removeAvatar) formData.append("removeAvatar", "true");

  const avatar = incoming.get("avatar");
  if (avatar instanceof File && avatar.size > 0) {
    const renamed = nameAvatarFile(avatar);
    formData.append("avatar", renamed, renamed.name);
  }

  const response = await fetch(`${getApiBase()}/me/`, {
    method: "PUT",
    headers: { Authorization: auth },
    body: formData,
  });
  const payload = await response.json().catch(() => ({}));
  if (!response.ok) {
    throw createError({ statusCode: response.status, statusMessage: payload?.error?.message || "Update failed" });
  }

  const meResponse = await fetch(`${getApiBase()}/users/me`, {
    headers: { Authorization: auth },
    cache: "no-store",
  });
  setResponseStatus(event, meResponse.status);
  return meResponse.json();
});
