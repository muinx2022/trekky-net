<template>
  <main class="mx-auto flex min-h-[70vh] max-w-xl items-center px-4 py-10">
    <div class="w-full rounded-3xl border border-zinc-200 bg-white p-6 shadow-sm dark:border-slate-700 dark:bg-slate-900">
      <h1 class="text-2xl font-semibold text-slate-900 dark:text-slate-100">Đặt lại mật khẩu</h1>
      <p class="mt-2 text-sm text-slate-500 dark:text-slate-400">
        Nhập mật khẩu mới cho tài khoản của bạn.
      </p>

      <form class="mt-6 space-y-4" @submit.prevent="submit">
        <label class="block text-sm">
          <span class="mb-1 block text-slate-700 dark:text-slate-200">Mật khẩu mới</span>
          <input
            v-model="password"
            type="password"
            required
            class="w-full rounded-xl border border-slate-300 px-3 py-2.5 outline-none transition focus:border-sky-500 focus:ring-2 focus:ring-sky-100 dark:border-slate-600 dark:bg-slate-950 dark:text-slate-100 dark:focus:ring-sky-900/40"
          />
        </label>

        <label class="block text-sm">
          <span class="mb-1 block text-slate-700 dark:text-slate-200">Nhập lại mật khẩu mới</span>
          <input
            v-model="confirmPassword"
            type="password"
            required
            class="w-full rounded-xl border border-slate-300 px-3 py-2.5 outline-none transition focus:border-sky-500 focus:ring-2 focus:ring-sky-100 dark:border-slate-600 dark:bg-slate-950 dark:text-slate-100 dark:focus:ring-sky-900/40"
          />
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
          {{ pending ? "Đang xử lý..." : "Cập nhật mật khẩu" }}
        </button>
      </form>

      <div class="mt-4 text-sm">
        <NuxtLink to="/" class="text-sky-600 hover:text-sky-700 dark:text-sky-300 dark:hover:text-sky-200">
          Quay về trang chủ
        </NuxtLink>
      </div>
    </div>
  </main>
</template>

<script setup lang="ts">
useSeoMeta({
  title: "Đặt lại mật khẩu",
  robots: "noindex, nofollow",
});

const route = useRoute();
const auth = useAuth();
const password = ref("");
const confirmPassword = ref("");
const errorMessage = ref("");
const successMessage = ref("");
const pending = ref(false);

async function submit() {
  errorMessage.value = "";
  successMessage.value = "";

  if (password.value !== confirmPassword.value) {
    errorMessage.value = "Mật khẩu nhập lại chưa khớp.";
    return;
  }

  const uid = String(route.query.uid || "");
  const token = String(route.query.token || "");
  if (!uid || !token) {
    errorMessage.value = "Liên kết đặt lại mật khẩu không hợp lệ.";
    return;
  }

  pending.value = true;
  const error = await auth.resetPassword(uid, token, password.value);
  pending.value = false;

  if (error) {
    errorMessage.value = error;
    return;
  }

  password.value = "";
  confirmPassword.value = "";
  successMessage.value = "Mật khẩu đã được cập nhật. Bạn có thể quay lại và đăng nhập bằng mật khẩu mới.";
}
</script>
