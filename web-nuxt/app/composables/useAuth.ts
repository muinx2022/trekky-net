import type { User } from "../../shared/types";

type DjangoMe = {
  id: number;
  email: string;
  username: string;
  bio?: string | null;
  avatar?: { url?: string | null } | string | null;
};

type AuthResponse = {
  access?: string;
  refresh?: string;
  message?: string;
};

const AUTH_STORAGE_KEY = "auth_user";
const AUTH_COOKIE_KEY = "trekky-auth";

function getAvatarFromMe(me: DjangoMe) {
  if (!me.avatar) return null;
  if (typeof me.avatar === "string") return { url: me.avatar };
  return me.avatar.url ? { url: me.avatar.url } : null;
}

export function useAuth() {
  const config = useRuntimeConfig();
  const authCookie = useCookie<string | null>(AUTH_COOKIE_KEY, {
    sameSite: "lax",
    path: "/",
    default: () => null,
  });
  const user = useState<User | null>("auth:user", () => readInitialUser(authCookie.value));
  const isLoginModalOpen = useState("auth:login-open", () => false);
  const isHydrated = useState("auth:hydrated", () => !!user.value || import.meta.server);

  function toAbsoluteMediaUrl(url?: string | null, version?: number | null) {
    if (!url) return null;
    const normalized = url.startsWith("http://") || url.startsWith("https://") ? url : `${config.public.apiUrl}${url}`;
    if (!version) return normalized;
    return normalized.includes("?") ? `${normalized}&v=${version}` : `${normalized}?v=${version}`;
  }

  function persist(nextUser: User | null, rememberMe = true) {
    authCookie.value = nextUser ? JSON.stringify(nextUser) : null;
    if (!import.meta.client) return;
    localStorage.removeItem(AUTH_STORAGE_KEY);
    sessionStorage.removeItem(AUTH_STORAGE_KEY);
    if (!nextUser) return;
    const storage = rememberMe ? localStorage : sessionStorage;
    storage.setItem(AUTH_STORAGE_KEY, JSON.stringify(nextUser));
  }

  function clearAuthState() {
    user.value = null;
    persist(null);
  }

  async function fetchCurrentUser(jwt: string): Promise<DjangoMe | null> {
    try {
      const response = await fetch("/api/me-proxy", {
        headers: { Authorization: `Bearer ${jwt}` },
        cache: "no-store",
      });
      if (!response.ok) return null;
      const me = (await response.json()) as Partial<DjangoMe>;
      if (!me.id || !me.email || !me.username) return null;
      return me as DjangoMe;
    } catch {
      return null;
    }
  }

  async function hydrateFromTokens(payload: AuthResponse, rememberMe: boolean) {
    if (!payload.access) return "Không thể xác thực tài khoản.";
    const me = await fetchCurrentUser(payload.access);
    if (!me) return "Không thể lấy thông tin tài khoản.";
    const avatar = getAvatarFromMe(me);
    user.value = {
      id: me.id,
      email: me.email,
      username: me.username,
      bio: me.bio ?? null,
      avatarId: null,
      avatarVersion: 0,
      avatarUrl: toAbsoluteMediaUrl(avatar?.url),
      jwt: payload.access,
      refreshToken: payload.refresh,
    };
    persist(user.value, rememberMe);
    isLoginModalOpen.value = false;
    return null;
  }

  async function login(email: string, password: string, rememberMe: boolean) {
    if (!email || !password) return "Vui lòng nhập email và mật khẩu.";
    try {
      const response = await fetch(`${config.public.apiUrl}/api/v1/auth/token/`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, password }),
      });
      if (!response.ok) {
        const payload = await response.json().catch(() => ({}));
        return payload?.detail || payload?.message || "Đăng nhập thất bại.";
      }
      return hydrateFromTokens((await response.json()) as AuthResponse, rememberMe);
    } catch {
      return "Không thể kết nối đến máy chủ.";
    }
  }

  async function register(email: string, username: string, password: string, rememberMe: boolean) {
    if (!email || !username || !password) return "Vui lòng điền đầy đủ thông tin đăng ký.";
    try {
      const response = await fetch(`${config.public.apiUrl}/api/v1/auth/register/`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, username, password }),
      });
      const payload = await response.json().catch(() => ({}));
      if (!response.ok) {
        const firstError = extractFirstError(payload);
        return firstError || payload?.detail || payload?.message || "Đăng ký thất bại.";
      }
      return hydrateFromTokens(payload as AuthResponse, rememberMe);
    } catch {
      return "Không thể kết nối đến máy chủ.";
    }
  }

  async function requestPasswordReset(email: string) {
    if (!email) return "Vui lòng nhập email để khôi phục mật khẩu.";
    try {
      const response = await fetch(`${config.public.apiUrl}/api/v1/auth/forgot-password/`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email }),
      });
      const payload = await response.json().catch(() => ({}));
      if (!response.ok) {
        return extractFirstError(payload) || payload?.detail || payload?.message || "Không thể gửi email khôi phục mật khẩu.";
      }
      return null;
    } catch {
      return "Không thể kết nối đến máy chủ.";
    }
  }

  async function resetPassword(uid: string, token: string, password: string) {
    if (!uid || !token || !password) return "Liên kết đặt lại mật khẩu không hợp lệ.";
    try {
      const response = await fetch(`${config.public.apiUrl}/api/v1/auth/reset-password/`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ uid, token, password }),
      });
      const payload = await response.json().catch(() => ({}));
      if (!response.ok) {
        return extractFirstError(payload) || payload?.detail || payload?.message || "Không thể đặt lại mật khẩu.";
      }
      return null;
    } catch {
      return "Không thể kết nối đến máy chủ.";
    }
  }

  async function loginWithToken(jwt: string, refreshToken?: string) {
    const me = await fetchCurrentUser(jwt);
    if (!me) return "Không thể lấy thông tin tài khoản.";
    const avatar = getAvatarFromMe(me);
    user.value = {
      id: me.id,
      email: me.email,
      username: me.username,
      bio: me.bio ?? null,
      avatarId: null,
      avatarVersion: 0,
      avatarUrl: toAbsoluteMediaUrl(avatar?.url),
      jwt,
      refreshToken,
    };
    persist(user.value, true);
    isLoginModalOpen.value = false;
    return null;
  }

  async function refreshSession() {
    if (!user.value?.refreshToken) return null;
    try {
      const response = await fetch(`${config.public.apiUrl}/api/v1/auth/token/refresh/`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ refresh: user.value.refreshToken }),
      });
      if (!response.ok) {
        clearAuthState();
        return null;
      }
      const payload = (await response.json()) as { access?: string };
      if (!payload.access) {
        clearAuthState();
        return null;
      }
      const me = await fetchCurrentUser(payload.access);
      if (!me) {
        clearAuthState();
        return null;
      }
      const avatar = getAvatarFromMe(me);
      user.value = {
        ...user.value,
        id: me.id,
        email: me.email,
        username: me.username,
        bio: me.bio ?? null,
        avatarUrl: toAbsoluteMediaUrl(avatar?.url, user.value.avatarVersion ?? 0),
        jwt: payload.access,
      };
      const remember = import.meta.client && !!localStorage.getItem(AUTH_STORAGE_KEY);
      persist(user.value, remember);
      return payload.access;
    } catch {
      return null;
    }
  }

  async function authorizedFetch(input: RequestInfo | URL, init: RequestInit = {}) {
    const execute = async (token: string) =>
      fetch(input, {
        ...init,
        headers: {
          ...(init.headers ?? {}),
          Authorization: `Bearer ${token}`,
        },
      });

    if (!user.value?.jwt) {
      return new Response(JSON.stringify({ error: "Unauthorized" }), {
        status: 401,
        headers: { "Content-Type": "application/json" },
      });
    }

    let response = await execute(user.value.jwt);
    if (response.status !== 401) return response;

    const nextJwt = await refreshSession();
    if (!nextJwt) {
      clearAuthState();
      return new Response(JSON.stringify({ error: "Unauthorized" }), {
        status: 401,
        headers: { "Content-Type": "application/json" },
      });
    }

    response = await execute(nextJwt);
    if (response.status === 401) clearAuthState();
    return response;
  }

  async function updateProfile(input: { bio: string; avatarFile: File | null; removeAvatar?: boolean }) {
    if (!user.value?.jwt) return "Bạn chưa đăng nhập.";
    try {
      const formData = new FormData();
      formData.append("bio", input.bio.trim());
      if (input.avatarFile) formData.append("avatar", input.avatarFile);
      if (input.removeAvatar) formData.append("removeAvatar", "true");
      const response = await authorizedFetch("/api/profile-proxy", {
        method: "PUT",
        body: formData,
      });
      if (!response.ok) {
        const payload = await response.json().catch(() => ({}));
        if (response.status === 401) {
          clearAuthState();
          return "Phiên đăng nhập đã hết hạn.";
        }
        return payload?.error || payload?.message || "Cập nhật hồ sơ thất bại.";
      }
      const payload = (await response.json()) as Partial<DjangoMe>;
      const avatar = getAvatarFromMe(payload as DjangoMe);
      const nextAvatarVersion = input.avatarFile || input.removeAvatar ? Date.now() : user.value.avatarVersion ?? 0;
      user.value = {
        ...user.value,
        id: payload.id ?? user.value.id,
        username: payload.username ?? user.value.username,
        email: payload.email ?? user.value.email,
        bio: payload.bio ?? null,
        avatarVersion: nextAvatarVersion,
        avatarUrl: toAbsoluteMediaUrl(avatar?.url, nextAvatarVersion),
      };
      const remember = import.meta.client && !!localStorage.getItem(AUTH_STORAGE_KEY);
      persist(user.value, remember);
      return null;
    } catch {
      return "Không thể cập nhật hồ sơ.";
    }
  }

  async function logout() {
    if (user.value?.refreshToken) {
      try {
        await fetch(`${config.public.apiUrl}/api/v1/auth/token/logout/`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ refresh: user.value.refreshToken }),
        });
      } catch {
        // ignore
      }
    }
    clearAuthState();
  }

  function restore() {
    if (!import.meta.client) {
      isHydrated.value = true;
      return;
    }
    if (user.value) {
      authCookie.value = JSON.stringify(user.value);
      isHydrated.value = true;
      return;
    }
    const raw = localStorage.getItem(AUTH_STORAGE_KEY) || sessionStorage.getItem(AUTH_STORAGE_KEY) || authCookie.value;
    if (!raw) {
      isHydrated.value = true;
      return;
    }
    try {
      user.value = readInitialUser(raw);
      if (user.value) authCookie.value = JSON.stringify(user.value);
    } catch {
      clearAuthState();
    } finally {
      isHydrated.value = true;
    }
  }

  return {
    user,
    isHydrated,
    isLoggedIn: computed(() => !!user.value),
    jwt: computed(() => user.value?.jwt ?? null),
    isLoginModalOpen,
    openLoginModal: () => (isLoginModalOpen.value = true),
    closeLoginModal: () => (isLoginModalOpen.value = false),
    restore,
    login,
    register,
    requestPasswordReset,
    resetPassword,
    loginWithToken,
    refreshSession,
    authorizedFetch,
    updateProfile,
    logout,
  };
}

function extractFirstError(payload: Record<string, unknown>) {
  for (const value of Object.values(payload ?? {})) {
    if (Array.isArray(value) && value.length && typeof value[0] === "string") return value[0];
    if (typeof value === "string") return value;
  }
  return null;
}

function readInitialUser(raw: string | null | undefined) {
  if (!raw) return null;
  try {
    const parsed = JSON.parse(raw) as Partial<User>;
    if (parsed.jwt && parsed.username && parsed.email) {
      return parsed as User;
    }
  } catch {
    return null;
  }
  return null;
}
