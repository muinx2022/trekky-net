<template>
  <div v-if="!accessToken && !errorParam" class="flex min-h-screen items-center justify-center">
    <div class="space-y-3 text-center">
      <p class="font-medium text-red-500">Khong nhan duoc token tu Google.</p>
      <button class="text-sm text-blue-600 hover:underline" @click="router.replace(resolveNextPath(nextParam))">Quay lai</button>
    </div>
  </div>
  <div v-else-if="error" class="flex min-h-screen items-center justify-center">
    <div class="space-y-3 text-center">
      <p class="font-medium text-red-500">{{ error }}</p>
      <button class="text-sm text-blue-600 hover:underline" @click="router.replace(resolveNextPath(nextParam))">Quay lai</button>
    </div>
  </div>
  <div v-else class="flex min-h-screen items-center justify-center">
    <div class="space-y-3 text-center">
      <svg class="mx-auto animate-spin text-blue-600" xmlns="http://www.w3.org/2000/svg" width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <path d="M21 12a9 9 0 1 1-6.219-8.56" />
      </svg>
      <p class="text-sm text-zinc-500">Dang xu ly dang nhap...</p>
    </div>
  </div>
</template>

<script setup lang="ts">
const route = useRoute();
const router = useRouter();
const auth = useAuth();
const error = ref<string | null>(null);
const accessToken = computed(() => (typeof route.query.access_token === "string" ? route.query.access_token : null));
const refreshToken = computed(() => (typeof route.query.refresh_token === "string" ? route.query.refresh_token : undefined));
const errorParam = computed(() => (typeof route.query.error === "string" ? route.query.error : null));
const nextParam = computed(() => (typeof route.query.next === "string" ? route.query.next : "/"));

function resolveNextPath(rawPath: string | null) {
  if (!rawPath) return "/";
  if (!rawPath.startsWith("/") || rawPath.startsWith("//")) return "/";
  return rawPath;
}

onMounted(() => {
  if (errorParam.value) {
    error.value = `Dang nhap Google that bai: ${errorParam.value}`;
    return;
  }
  if (!accessToken.value) return;
  void (async () => {
    const loginError = await auth.loginWithToken(accessToken.value!, refreshToken.value);
    if (loginError) {
      error.value = loginError;
      return;
    }
    await router.replace(resolveNextPath(nextParam.value));
  })();
});
</script>
