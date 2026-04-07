export function getDjangoUrl() {
  const config = useRuntimeConfig();
  return String(config.apiUrl).replace("http://localhost:8000", "http://127.0.0.1:8000");
}

export function getApiBase() {
  return `${getDjangoUrl()}/api/v1`;
}

export async function forwardJson(event: H3Event, target: string, init?: RequestInit) {
  const headers = new Headers(init?.headers);
  const auth = getHeader(event, "authorization");
  if (auth && !headers.has("authorization")) headers.set("authorization", auth);
  if (!headers.has("content-type") && init?.body && !(init.body instanceof FormData)) {
    headers.set("content-type", "application/json");
  }

  const response = await fetch(target, {
    ...init,
    headers,
  });

  const text = await response.text();
  setResponseStatus(event, response.status);
  const type = response.headers.get("content-type") ?? "application/json";
  setHeader(event, "content-type", type);

  if (!text) return null;
  if (type.includes("application/json")) return JSON.parse(text);
  return text;
}
