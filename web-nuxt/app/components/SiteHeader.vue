<template>
  <header class="sticky top-0 z-50 w-full border-b border-gray-200 bg-white shadow-md">
    <div class="container mx-auto flex h-16 items-center justify-between gap-4 px-4">
      <div class="flex shrink-0 items-center gap-2">
        <button type="button" class="flex items-center gap-2 md:hidden" aria-label="Mo menu" @click="drawer.openDrawer('right')">
          <div class="flex h-10 w-10 select-none items-center justify-center rounded-full bg-blue-600 text-lg font-bold text-white">T</div>
        </button>

        <NuxtLink to="/" class="hidden shrink-0 items-center gap-2 md:flex">
          <div class="flex h-10 w-10 select-none items-center justify-center rounded-full bg-blue-600 text-lg font-bold text-white">T</div>
          <span class="text-xl font-bold tracking-tight text-gray-900">Trekky</span>
        </NuxtLink>
      </div>

      <div class="mx-4 hidden max-w-md flex-1 md:flex">
        <SearchBox :on-search="handleSearch" />
      </div>

      <div class="flex items-center gap-1 md:gap-2">
        <button class="flex h-10 w-10 items-center justify-center rounded-full text-gray-600 hover:bg-gray-100 md:hidden" aria-label="Mo tim kiem" @click="searchOpen = !searchOpen">
          <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="11" cy="11" r="8" /><path d="m21 21-4.3-4.3" /></svg>
        </button>
        <button
          type="button"
          class="flex h-10 w-10 items-center justify-center rounded-full text-gray-600 transition-colors hover:bg-gray-100"
          :aria-label="theme.isDark.value ? 'Chuyen sang che do sang' : 'Chuyen sang che do toi'"
          @click="theme.toggleTheme()"
        >
          <svg v-if="theme.isDark.value" xmlns="http://www.w3.org/2000/svg" width="19" height="19" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <circle cx="12" cy="12" r="4" />
            <path d="M12 2v2" />
            <path d="M12 20v2" />
            <path d="m4.93 4.93 1.41 1.41" />
            <path d="m17.66 17.66 1.41 1.41" />
            <path d="M2 12h2" />
            <path d="M20 12h2" />
            <path d="m6.34 17.66-1.41 1.41" />
            <path d="m19.07 4.93-1.41 1.41" />
          </svg>
          <svg v-else xmlns="http://www.w3.org/2000/svg" width="19" height="19" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M12 3a6 6 0 0 0 9 9 9 9 0 1 1-9-9Z" />
          </svg>
        </button>
      </div>

      <div class="flex shrink-0 items-center gap-2">
        <div v-if="!auth.isHydrated.value" class="h-10 w-[140px]" />
        <template v-else-if="auth.isLoggedIn.value && auth.user.value">
          <NuxtLink to="/my-posts/new" class="hidden items-center gap-1.5 rounded-full bg-gray-500 px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-gray-600 sm:flex">
            Tao bai
          </NuxtLink>
          <NuxtLink to="/my-posts/new" class="flex h-10 w-10 items-center justify-center rounded-full bg-gray-500 text-white sm:hidden" aria-label="Tao bai">+</NuxtLink>

          <div ref="menuRef" class="relative">
            <button
              type="button"
              class="flex items-center gap-2 rounded-full border-2 border-gray-200 bg-gray-50 px-2 py-1 transition-colors hover:bg-gray-100"
              @click="menuOpen = !menuOpen"
            >
              <img v-if="auth.user.value.avatarUrl" :src="auth.user.value.avatarUrl" alt="Avatar" width="32" height="32" class="h-8 w-8 rounded-full border-2 border-white object-cover" />
              <div v-else class="flex h-8 w-8 items-center justify-center rounded-full border-2 border-white bg-gray-400 text-sm font-bold uppercase text-white">
                {{ (auth.user.value.username ?? auth.user.value.email)[0] }}
              </div>
              <span class="hidden text-sm font-medium text-gray-700 sm:block">{{ auth.user.value.username }}</span>
            </button>

            <div v-if="menuOpen" class="absolute right-0 mt-2 w-56 overflow-hidden rounded-xl border border-gray-200 bg-white shadow-xl">
              <div class="border-b border-gray-100 px-4 py-3">
                <p class="text-sm font-medium text-gray-900">{{ auth.user.value.username }}</p>
                <p class="text-xs text-gray-500">{{ auth.user.value.email }}</p>
              </div>
              <NuxtLink to="/my-posts/new" class="flex items-center gap-3 px-4 py-3 text-sm text-gray-700 hover:bg-gray-50" @click="menuOpen = false">Tao bai viet</NuxtLink>
              <NuxtLink to="/my-posts" class="flex items-center gap-3 px-4 py-3 text-sm text-gray-700 hover:bg-gray-50" @click="menuOpen = false">Bai viet cua toi</NuxtLink>
              <NuxtLink to="/profile/edit" class="flex items-center gap-3 px-4 py-3 text-sm text-gray-700 hover:bg-gray-50" @click="menuOpen = false">Sua ho so</NuxtLink>
              <div class="border-t border-gray-100">
                <button type="button" class="flex w-full items-center gap-3 px-4 py-3 text-left text-sm text-red-600 hover:bg-red-50" @click="logout">Dang xuat</button>
              </div>
            </div>
          </div>
        </template>
        <button v-else class="rounded-full bg-gray-500 px-5 py-2 text-sm font-medium text-white transition-colors hover:bg-gray-600" @click="auth.openLoginModal()">
          Dang nhap
        </button>
      </div>
    </div>

    <div v-if="searchOpen" class="animate-fade-in absolute left-0 right-0 top-16 border-t border-gray-100 bg-white p-4 shadow-lg md:hidden">
      <SearchBox :on-search="handleSearch" />
    </div>
  </header>
</template>

<script setup lang="ts">
const router = useRouter();
const auth = useAuth();
const drawer = useDrawer();
const theme = useTheme();
const menuOpen = ref(false);
const searchOpen = ref(false);
const menuRef = ref<HTMLElement | null>(null);
let onDocClick: ((event: MouseEvent) => void) | null = null;

function handleSearch(query: string) {
  router.push(`/search?q=${encodeURIComponent(query.trim())}`);
  searchOpen.value = false;
}

async function logout() {
  menuOpen.value = false;
  await auth.logout();
}

onMounted(() => {
  onDocClick = (event: MouseEvent) => {
    if (!menuRef.value || menuRef.value.contains(event.target as Node)) return;
    menuOpen.value = false;
  };
  document.addEventListener("mousedown", onDocClick);
});

onBeforeUnmount(() => {
  if (onDocClick) document.removeEventListener("mousedown", onDocClick);
});
</script>
