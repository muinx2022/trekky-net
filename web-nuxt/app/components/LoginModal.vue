<template>
  <Teleport to="body">
    <div v-if="auth.isLoginModalOpen.value" class="fixed inset-0 z-[100] flex items-center justify-center">
      <div class="absolute inset-0 bg-black/50 backdrop-blur-sm" aria-hidden="true" @click="auth.closeLoginModal()" />

      <div class="relative w-full max-w-sm rounded-2xl border border-zinc-200 bg-white p-6 shadow-2xl">
        <div class="flex items-start justify-between gap-4">
          <div>
            <h2 class="text-xl font-semibold text-slate-900">Dang nhap</h2>
            <p class="mt-1 text-sm text-slate-500">Chao mung ban tro lai!</p>
          </div>
          <button class="text-sm text-slate-500 hover:text-slate-900" @click="auth.closeLoginModal()">Dong</button>
        </div>

        <form class="mt-5 space-y-4" @submit.prevent="submit">
          <label class="block text-sm">
            <span class="mb-1 block text-slate-700">Email</span>
            <input v-model="email" type="email" required class="w-full rounded-xl border border-slate-300 px-3 py-2 outline-none focus:border-sky-500" />
          </label>

          <label class="block text-sm">
            <span class="mb-1 block text-slate-700">Mat khau</span>
            <input v-model="password" type="password" required class="w-full rounded-xl border border-slate-300 px-3 py-2 outline-none focus:border-sky-500" />
          </label>

          <label class="flex items-center gap-2 text-sm text-slate-600">
            <input v-model="rememberMe" type="checkbox" class="rounded border-slate-300" />
            Ghi nho dang nhap
          </label>

          <p v-if="errorMessage" class="rounded-xl bg-rose-50 px-3 py-2 text-sm text-rose-700">{{ errorMessage }}</p>

          <button
            type="submit"
            class="w-full rounded-xl bg-sky-600 px-4 py-2.5 text-sm font-medium text-white transition hover:bg-sky-700 disabled:cursor-not-allowed disabled:bg-slate-300"
            :disabled="pending"
          >
            {{ pending ? "Dang xu ly..." : "Dang nhap" }}
          </button>

          <a
            :href="googleAuthHref"
            class="flex w-full items-center justify-center gap-2.5 rounded-lg border border-zinc-200 bg-white py-2.5 text-sm font-medium text-zinc-700 transition-colors hover:bg-zinc-50"
          >
            Dang nhap bang Google
          </a>
        </form>
      </div>
    </div>
  </Teleport>
</template>

<script setup lang="ts">
const route = useRoute();
const runtimeConfig = useRuntimeConfig();
const auth = useAuth();
const email = ref("");
const password = ref("");
const rememberMe = ref(true);
const errorMessage = ref("");
const pending = ref(false);

const currentReturnTo = computed(() => `${route.path}${typeof route.fullPath === "string" ? route.fullPath.slice(route.path.length) : ""}`);
const googleAuthHref = computed(
  () =>
    `${runtimeConfig.public.apiUrl}/api/v1/auth/google/?frontend_url=${encodeURIComponent(import.meta.client ? window.location.origin : runtimeConfig.public.baseUrl)}&return_to=${encodeURIComponent(currentReturnTo.value || "/")}`,
);

async function submit() {
  pending.value = true;
  errorMessage.value = "";
  const error = await auth.login(email.value, password.value, rememberMe.value);
  pending.value = false;
  if (error) errorMessage.value = error;
}
</script>
