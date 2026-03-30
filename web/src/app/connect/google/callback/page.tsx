"use client";

import { Suspense, useEffect, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { useAuth } from "@/components/auth-context";

function GoogleCallbackInner() {
  const searchParams = useSearchParams();
  const router = useRouter();
  const { loginWithToken } = useAuth();
  const [error, setError] = useState<string | null>(null);
  const accessToken = searchParams.get("access_token");
  const refreshToken = searchParams.get("refresh_token") ?? undefined;
  const errorParam = searchParams.get("error");

  useEffect(() => {
    if (errorParam) {
      setError("Đăng nhập Google thất bại: " + errorParam);
      return;
    }
    if (!accessToken) {
      return;
    }

    (async () => {
      const loginError = await loginWithToken(accessToken, refreshToken);
      if (loginError) {
        setError(loginError);
        return;
      }
      router.replace("/");
    })();
  }, [accessToken, refreshToken, errorParam, loginWithToken, router]);

  if (!accessToken && !errorParam) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center space-y-3">
          <p className="text-red-500 font-medium">Không nhận được token từ Google.</p>
          <button
            onClick={() => router.replace("/")}
            className="text-sm text-blue-600 hover:underline"
          >
            Quay về trang chủ
          </button>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center space-y-3">
          <p className="text-red-500 font-medium">{error}</p>
          <button
            onClick={() => router.replace("/")}
            className="text-sm text-blue-600 hover:underline"
          >
            Quay về trang chủ
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen flex items-center justify-center">
      <div className="text-center space-y-3">
        <svg
          className="animate-spin mx-auto text-blue-600"
          xmlns="http://www.w3.org/2000/svg"
          width="28"
          height="28"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          strokeWidth="2"
          strokeLinecap="round"
          strokeLinejoin="round"
        >
          <path d="M21 12a9 9 0 1 1-6.219-8.56" />
        </svg>
        <p className="text-sm text-zinc-500">Đang xử lý đăng nhập...</p>
      </div>
    </div>
  );
}

export default function GoogleCallbackPage() {
  return (
    <Suspense
      fallback={
        <div className="min-h-screen flex items-center justify-center">
          <svg
            className="animate-spin text-blue-600"
            xmlns="http://www.w3.org/2000/svg"
            width="28"
            height="28"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
            strokeLinecap="round"
            strokeLinejoin="round"
          >
            <path d="M21 12a9 9 0 1 1-6.219-8.56" />
          </svg>
        </div>
      }
    >
      <GoogleCallbackInner />
    </Suspense>
  );
}
