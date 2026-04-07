<template>
  <Teleport to="body">
    <div v-if="auth.isLoginModalOpen.value" class="fixed inset-0 z-[100] flex items-center justify-center p-4">
      <div class="absolute inset-0 bg-black/50 backdrop-blur-sm" aria-hidden="true" @click="closeModal" />

      <div class="relative w-full max-w-md rounded-3xl border border-zinc-200 bg-white p-6 shadow-2xl dark:border-slate-700 dark:bg-slate-900">
        <div class="flex items-start justify-between gap-4">
          <div>
            <h2 class="text-xl font-semibold text-slate-900 dark:text-slate-100">{{ panelTitle }}</h2>
            <p class="mt-1 text-sm text-slate-500 dark:text-slate-400">{{ panelDescription }}</p>
          </div>
          <button class="text-sm text-slate-500 transition-colors hover:text-slate-900 dark:text-slate-400 dark:hover:text-slate-100" @click="closeModal">
            Đóng
          </button>
        </div>

        <div class="mt-5 space-y-4">
          <a
            v-if="mode !== 'forgot'"
            :href="googleAuthHref"
            class="group flex w-full items-center justify-center gap-3 rounded-2xl border border-zinc-200 bg-[linear-gradient(135deg,#ffffff_0%,#f8fafc_100%)] px-4 py-3 text-sm font-semibold text-slate-700 shadow-sm transition-all hover:-translate-y-0.5 hover:border-sky-200 hover:shadow-md dark:border-slate-700 dark:bg-[linear-gradient(135deg,#0f172a_0%,#111827_100%)] dark:text-slate-200 dark:hover:border-sky-500/50 dark:hover:shadow-sky-950/30"
          >
            <span class="flex h-9 w-9 items-center justify-center rounded-full bg-white shadow-sm ring-1 ring-zinc-200 dark:bg-slate-950 dark:ring-slate-700">
              <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 48 48" class="h-5 w-5" aria-hidden="true">
                <path fill="#FFC107" d="M43.6 20.5H42V20H24v8h11.3C33.6 32.7 29.2 36 24 36c-6.6 0-12-5.4-12-12s5.4-12 12-12c3 0 5.7 1.1 7.8 3l5.7-5.7C34.1 6.1 29.3 4 24 4 12.9 4 4 12.9 4 24s8.9 20 20 20 20-8.9 20-20c0-1.3-.1-2.4-.4-3.5Z" />
                <path fill="#FF3D00" d="M6.3 14.7 12.9 19.5C14.7 15.1 19 12 24 12c3 0 5.7 1.1 7.8 3l5.7-5.7C34.1 6.1 29.3 4 24 4 16.3 4 9.7 8.3 6.3 14.7Z" />
                <path fill="#4CAF50" d="M24 44c5.2 0 9.9-2 13.4-5.2l-6.2-5.2C29.2 35.1 26.7 36 24 36c-5.2 0-9.6-3.3-11.3-8l-6.5 5C9.5 39.6 16.2 44 24 44Z" />
                <path fill="#1976D2" d="M43.6 20.5H42V20H24v8h11.3c-.8 2.3-2.2 4.2-4.1 5.6l.1-.1 6.2 5.2C37.1 39 44 34 44 24c0-1.3-.1-2.4-.4-3.5Z" />
              </svg>
            </span>
            <span class="flex flex-col items-start leading-tight">
              <span class="text-slate-900 dark:text-slate-100">Tiếp tục với Google</span>
              <span class="text-xs font-medium text-slate-500 dark:text-slate-400">Đăng nhập nhanh, hỗ trợ cả giao diện sáng và tối</span>
            </span>
          </a>

          <div v-if="mode !== 'forgot'" class="flex items-center gap-3">
            <div class="h-px flex-1 bg-zinc-200 dark:bg-slate-700" />
            <span class="text-xs font-semibold uppercase tracking-[0.24em] text-zinc-400 dark:text-slate-500">Hoặc</span>
            <div class="h-px flex-1 bg-zinc-200 dark:bg-slate-700" />
          </div>

          <form class="space-y-4" @submit.prevent="submit">
            <label class="block text-sm">
              <span class="mb-1 block text-slate-700 dark:text-slate-200">Email</span>
              <input
                v-model="email"
                type="email"
                required
                class="w-full rounded-xl border border-slate-300 px-3 py-2.5 outline-none transition focus:border-sky-500 focus:ring-2 focus:ring-sky-100 dark:border-slate-600 dark:bg-slate-950 dark:text-slate-100 dark:focus:ring-sky-900/40"
              />
            </label>

            <label v-if="mode === 'register'" class="block text-sm">
              <span class="mb-1 block text-slate-700 dark:text-slate-200">Tên người dùng</span>
              <input
                v-model="username"
                type="text"
                required
                class="w-full rounded-xl border border-slate-300 px-3 py-2.5 outline-none transition focus:border-sky-500 focus:ring-2 focus:ring-sky-100 dark:border-slate-600 dark:bg-slate-950 dark:text-slate-100 dark:focus:ring-sky-900/40"
              />
            </label>

            <label v-if="mode !== 'forgot'" class="block text-sm">
              <span class="mb-1 block text-slate-700 dark:text-slate-200">Mật khẩu</span>
              <input
                v-model="password"
                type="password"
                required
                class="w-full rounded-xl border border-slate-300 px-3 py-2.5 outline-none transition focus:border-sky-500 focus:ring-2 focus:ring-sky-100 dark:border-slate-600 dark:bg-slate-950 dark:text-slate-100 dark:focus:ring-sky-900/40"
              />
            </label>

            <label v-if="mode === 'register'" class="block text-sm">
              <span class="mb-1 block text-slate-700 dark:text-slate-200">Nhập lại mật khẩu</span>
              <input
                v-model="confirmPassword"
                type="password"
                required
                class="w-full rounded-xl border border-slate-300 px-3 py-2.5 outline-none transition focus:border-sky-500 focus:ring-2 focus:ring-sky-100 dark:border-slate-600 dark:bg-slate-950 dark:text-slate-100 dark:focus:ring-sky-900/40"
              />
            </label>

            <label v-if="mode !== 'forgot'" class="flex items-center gap-2 text-sm text-slate-600 dark:text-slate-300">
              <input v-model="rememberMe" type="checkbox" class="rounded border-slate-300 dark:border-slate-600" />
              Ghi nhớ đăng nhập
            </label>

            <p v-if="successMessage" class="rounded-xl bg-emerald-50 px-3 py-2 text-sm text-emerald-700 dark:bg-emerald-950/40 dark:text-emerald-300">
              {{ successMessage }}
            </p>

            <p v-if="errorMessage" class="rounded-xl bg-rose-50 px-3 py-2 text-sm text-rose-700 dark:bg-rose-950/40 dark:text-rose-300">
              {{ errorMessage }}
            </p>

            <button
              type="submit"
              class="w-full rounded-xl bg-sky-600 px-4 py-2.5 text-sm font-medium text-white transition hover:bg-sky-700 disabled:cursor-not-allowed disabled:bg-slate-300 dark:disabled:bg-slate-700"
              :disabled="pending"
            >
              {{ pending ? "Đang xử lý..." : submitLabel }}
            </button>
          </form>

          <div class="flex flex-wrap items-center justify-between gap-3 border-t border-zinc-200 pt-4 text-sm dark:border-slate-700">
            <button v-if="mode !== 'login'" class="text-slate-500 transition hover:text-sky-600 dark:text-slate-400 dark:hover:text-sky-300" @click="setMode('login')">
              Quay lại đăng nhập
            </button>
            <button v-else class="text-slate-500 transition hover:text-sky-600 dark:text-slate-400 dark:hover:text-sky-300" @click="setMode('forgot')">
              Quên mật khẩu?
            </button>

            <button v-if="mode === 'login'" class="text-slate-700 transition hover:text-sky-600 dark:text-slate-200 dark:hover:text-sky-300" @click="setMode('register')">
              Tạo tài khoản mới
            </button>
            <button v-else-if="mode === 'register'" class="text-slate-700 transition hover:text-sky-600 dark:text-slate-200 dark:hover:text-sky-300" @click="setMode('forgot')">
              Quên mật khẩu
            </button>
          </div>
        </div>
      </div>
    </div>
  </Teleport>
</template>

<script setup lang="ts">
type AuthMode = "login" | "register" | "forgot";

const route = useRoute();
const runtimeConfig = useRuntimeConfig();
const auth = useAuth();

const mode = ref<AuthMode>("login");
const email = ref("");
const username = ref("");
const password = ref("");
const confirmPassword = ref("");
const rememberMe = ref(true);
const errorMessage = ref("");
const successMessage = ref("");
const pending = ref(false);

const currentReturnTo = computed(() => `${route.path}${typeof route.fullPath === "string" ? route.fullPath.slice(route.path.length) : ""}`);
const googleAuthHref = computed(
  () =>
    `${runtimeConfig.public.apiUrl}/api/v1/auth/google/?frontend_url=${encodeURIComponent(import.meta.client ? window.location.origin : runtimeConfig.public.baseUrl)}&return_to=${encodeURIComponent(currentReturnTo.value || "/")}`,
);

const panelTitle = computed(() => {
  if (mode.value === "register") return "Tạo tài khoản";
  if (mode.value === "forgot") return "Khôi phục mật khẩu";
  return "Đăng nhập";
});

const panelDescription = computed(() => {
  if (mode.value === "register") return "Tạo tài khoản mới để bình luận, theo dõi và quản lý bài viết của bạn.";
  if (mode.value === "forgot") return "Nhập email của bạn, chúng tôi sẽ gửi liên kết đặt lại mật khẩu.";
  return "Chào mừng bạn quay lại Trekky.";
});

const submitLabel = computed(() => {
  if (mode.value === "register") return "Đăng ký";
  if (mode.value === "forgot") return "Gửi email khôi phục";
  return "Đăng nhập";
});

function resetMessages() {
  errorMessage.value = "";
  successMessage.value = "";
}

function resetForm(keepEmail = false) {
  if (!keepEmail) email.value = "";
  username.value = "";
  password.value = "";
  confirmPassword.value = "";
  resetMessages();
}

function setMode(nextMode: AuthMode) {
  mode.value = nextMode;
  resetForm(nextMode === "forgot");
}

function closeModal() {
  auth.closeLoginModal();
  mode.value = "login";
  resetForm();
}

watch(
  () => auth.isLoginModalOpen.value,
  (isOpen) => {
    if (isOpen) {
      mode.value = "login";
      resetForm();
    }
  },
);

async function submit() {
  pending.value = true;
  resetMessages();

  if (mode.value === "register" && password.value !== confirmPassword.value) {
    pending.value = false;
    errorMessage.value = "Mật khẩu nhập lại chưa khớp.";
    return;
  }

  if (mode.value === "forgot") {
    const error = await auth.requestPasswordReset(email.value);
    pending.value = false;
    if (error) {
      errorMessage.value = error;
      return;
    }
    successMessage.value = "Nếu email tồn tại trong hệ thống, liên kết đặt lại mật khẩu đã được gửi.";
    return;
  }

  const error =
    mode.value === "register"
      ? await auth.register(email.value, username.value, password.value, rememberMe.value)
      : await auth.login(email.value, password.value, rememberMe.value);

  pending.value = false;
  if (error) errorMessage.value = error;
}
</script>
