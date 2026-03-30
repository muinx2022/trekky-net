"use client";

import { createContext, useContext, useState, useCallback, ReactNode } from "react";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";
const API_BASE = `${API_URL}/api/v1`;

type Media = {
  id?: number;
  url?: string | null;
};

// Django LegacyMeView returns: { id, username, email, bio, avatar: { url } | null }
type DjangoMe = {
  id: number;
  email: string;
  username: string;
  bio?: string | null;
  avatar?: { url?: string | null } | string | null;
};

export type User = {
  id: number;
  email: string;
  username: string;
  bio?: string | null;
  avatarId?: number | null;
  avatarUrl?: string | null;
  avatarVersion?: number;
  /** The Django Simple JWT access token */
  jwt: string;
  /** The Django refresh token (for logout) */
  refreshToken?: string;
};

type AuthContextType = {
  user: User | null;
  isLoggedIn: boolean;
  jwt: string | null;
  login: (email: string, password: string, rememberMe: boolean) => Promise<string | null>;
  loginWithToken: (jwt: string, refreshToken?: string) => Promise<string | null>;
  refreshSession: () => Promise<string | null>;
  authorizedFetch: (input: RequestInfo | URL, init?: RequestInit) => Promise<Response>;
  updateProfile: (input: { bio: string; avatarFile: File | null }) => Promise<string | null>;
  logout: () => void;
  isLoginModalOpen: boolean;
  openLoginModal: () => void;
  closeLoginModal: () => void;
};

const AuthContext = createContext<AuthContextType | null>(null);

function getAvatarFromMe(me: DjangoMe): Media | null {
  if (!me.avatar) return null;
  if (typeof me.avatar === "string") return { url: me.avatar };
  if (typeof me.avatar === "object" && me.avatar.url) return { url: me.avatar.url };
  return null;
}

function toAbsoluteMediaUrl(url?: string | null, version?: number | null) {
  if (!url) return null;
  const normalized = url.startsWith("http://") || url.startsWith("https://") ? url : `${API_URL}${url}`;
  if (!version) return normalized;
  return normalized.includes("?") ? `${normalized}&v=${version}` : `${normalized}?v=${version}`;
}

function unauthorizedResponse() {
  return new Response(JSON.stringify({ error: "Unauthorized" }), {
    status: 401,
    headers: { "Content-Type": "application/json" },
  });
}

async function fetchCurrentUser(jwt: string): Promise<DjangoMe | null> {
  try {
    const url = typeof window !== "undefined"
      ? "/api/me-proxy"
      : `${API_BASE}/users/me`;
    const res = await fetch(url, {
      headers: { Authorization: `Bearer ${jwt}` },
      cache: "no-store",
    });
    if (!res.ok) return null;
    const me = (await res.json()) as Partial<DjangoMe>;
    if (!me.id || !me.email || !me.username) return null;
    return me as DjangoMe;
  } catch {
    return null;
  }
}

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(() => {
    if (typeof window === "undefined") return null;
    const stored = localStorage.getItem("auth_user") || sessionStorage.getItem("auth_user");
    if (!stored) return null;
    try {
      const parsed = JSON.parse(stored) as Partial<User>;
      if (parsed.jwt && parsed.username && parsed.email) return parsed as User;
    } catch {
      // fall through
    }
    localStorage.removeItem("auth_user");
    sessionStorage.removeItem("auth_user");
    return null;
  });

  const [isLoginModalOpen, setIsLoginModalOpen] = useState(false);

  const clearAuthState = useCallback(() => {
    setUser(null);
    localStorage.removeItem("auth_user");
    sessionStorage.removeItem("auth_user");
  }, []);

  const login = useCallback(
    async (email: string, password: string, rememberMe: boolean): Promise<string | null> => {
      if (!email || !password) return "Vui lòng nhập email và mật khẩu.";

      let res: Response;
      try {
        // Django Simple JWT: USERNAME_FIELD=email → field name is "email"
        res = await fetch(`${API_BASE}/auth/token/`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ email, password }),
        });
      } catch {
        return "Không thể kết nối đến máy chủ. Vui lòng thử lại.";
      }

      if (!res.ok) {
        try {
          const err = await res.json();
          const msg =
            err?.detail ||
            err?.error?.message ||
            err?.message ||
            "Email hoặc mật khẩu không đúng.";
          return msg;
        } catch {
          return "Đăng nhập thất bại. Vui lòng thử lại.";
        }
      }

      // Django Simple JWT returns { access, refresh }
      const data = await res.json();
      const accessToken = data.access as string;
      const refreshToken = data.refresh as string;

      if (!accessToken) return "Đăng nhập thất bại. Vui lòng thử lại.";

      const me = await fetchCurrentUser(accessToken);
      if (!me) return "Không thể lấy thông tin tài khoản.";

      const avatar = getAvatarFromMe(me);
      const u: User = {
        id: me.id,
        email: me.email,
        username: me.username,
        bio: me.bio ?? null,
        avatarId: null,
        avatarVersion: 0,
        avatarUrl: toAbsoluteMediaUrl(avatar?.url),
        jwt: accessToken,
        refreshToken,
      };

      setUser(u);
      const storage = rememberMe ? localStorage : sessionStorage;
      storage.setItem("auth_user", JSON.stringify(u));
      setIsLoginModalOpen(false);
      return null;
    },
    [],
  );

  const loginWithToken = useCallback(async (jwt: string, refreshToken?: string): Promise<string | null> => {
    const me = await fetchCurrentUser(jwt);
    if (!me) return "Không thể lấy thông tin tài khoản.";
    const avatar = getAvatarFromMe(me);
    const u: User = {
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
    setUser(u);
    localStorage.setItem("auth_user", JSON.stringify(u));
    setIsLoginModalOpen(false);
    return null;
  }, []);

  const refreshSession = useCallback(async (): Promise<string | null> => {
    if (!user?.refreshToken) return null;

    let res: Response;
    try {
      res = await fetch(`${API_BASE}/auth/token/refresh/`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ refresh: user.refreshToken }),
      });
    } catch {
      return null;
    }

    if (!res.ok) {
      clearAuthState();
      return null;
    }

    const payload = (await res.json().catch(() => ({}))) as { access?: string };
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
    const nextUser: User = {
      ...user,
      id: me.id,
      email: me.email,
      username: me.username,
      bio: me.bio ?? null,
      avatarUrl: toAbsoluteMediaUrl(avatar?.url, user.avatarVersion ?? 0),
      jwt: payload.access,
    };

    setUser(nextUser);
    if (localStorage.getItem("auth_user")) localStorage.setItem("auth_user", JSON.stringify(nextUser));
    if (sessionStorage.getItem("auth_user")) sessionStorage.setItem("auth_user", JSON.stringify(nextUser));
    return payload.access;
  }, [user, clearAuthState]);

  const authorizedFetch = useCallback(
    async (input: RequestInfo | URL, init: RequestInit = {}) => {
      const run = async (accessToken: string) =>
        fetch(input, {
          ...init,
          headers: {
            ...(init.headers ?? {}),
            Authorization: `Bearer ${accessToken}`,
          },
        });

      const currentJwt = user?.jwt;
      if (!currentJwt) return unauthorizedResponse();

      let response = await run(currentJwt);
      if (response.status !== 401) return response;

      const refreshedJwt = await refreshSession();
      if (!refreshedJwt) return unauthorizedResponse();

      response = await run(refreshedJwt);
      if (response.status === 401) {
        clearAuthState();
        return unauthorizedResponse();
      }

      return response;
    },
    [user?.jwt, refreshSession, clearAuthState],
  );

  const updateProfile = useCallback(
    async (input: { bio: string; avatarFile: File | null }): Promise<string | null> => {
      if (!user?.jwt) return "Bạn chưa đăng nhập.";

      let res: Response;
      try {
        const formData = new FormData();
        formData.append("bio", input.bio.trim());
        if (input.avatarFile) formData.append("avatar", input.avatarFile);

        res = await authorizedFetch("/api/profile-proxy", {
          method: "PUT",
          body: formData,
        });
      } catch {
        return "Không thể cập nhật hồ sơ. Vui lòng thử lại.";
      }

      if (!res.ok) {
        if (res.status === 401) {
          clearAuthState();
          return "Phiên đăng nhập đã hết hạn. Vui lòng đăng nhập lại.";
        }
        try {
          const payload = await res.json();
          return payload?.error || payload?.message || "Cập nhật hồ sơ thất bại.";
        } catch {
          return "Cập nhật hồ sơ thất bại.";
        }
      }

      const payload = (await res.json()) as Partial<DjangoMe>;
      const avatar = getAvatarFromMe(payload as DjangoMe);
      const nextAvatarVersion = input.avatarFile ? Date.now() : user.avatarVersion ?? 0;
      const nextUser: User = {
        ...user,
        id: payload.id ?? user.id,
        username: payload.username ?? user.username,
        email: payload.email ?? user.email,
        bio: payload.bio ?? null,
        avatarVersion: nextAvatarVersion,
        avatarUrl: toAbsoluteMediaUrl(avatar?.url, nextAvatarVersion),
      };

      setUser(nextUser);
      if (localStorage.getItem("auth_user")) localStorage.setItem("auth_user", JSON.stringify(nextUser));
      if (sessionStorage.getItem("auth_user")) sessionStorage.setItem("auth_user", JSON.stringify(nextUser));

      return null;
    },
    [user, clearAuthState, authorizedFetch],
  );

  const logout = useCallback(async () => {
    if (user?.refreshToken) {
      try {
        await fetch(`${API_BASE}/auth/token/logout/`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ refresh: user.refreshToken }),
        });
      } catch {
        // Ignore logout errors
      }
    }
    clearAuthState();
  }, [user, clearAuthState]);

  return (
    <AuthContext.Provider
      value={{
        user,
        isLoggedIn: !!user,
        jwt: user?.jwt ?? null,
        login,
        loginWithToken,
        refreshSession,
        authorizedFetch,
        updateProfile,
        logout,
        isLoginModalOpen,
        openLoginModal: () => setIsLoginModalOpen(true),
        closeLoginModal: () => setIsLoginModalOpen(false),
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within AuthProvider");
  return ctx;
}
