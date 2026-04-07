<template>
  <div :class="wrapperClass">
    <button
      type="button"
      class="flex items-center gap-2 rounded-full px-3 py-1.5 text-sm font-medium transition-colors"
      :class="likeClass"
      :disabled="pendingAction === 'like'"
      @click="toggleInteraction('like')"
    >
      <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" :fill="liked ? 'currentColor' : 'none'" stroke="currentColor" stroke-width="2">
        <path d="M19 14c1.49-1.46 3-3.21 3-5.5A5.5 5.5 0 0 0 16.5 3c-1.76 0-3 .5-4.5 2-1.5-1.5-2.74-2-4.5-2A5.5 5.5 0 0 0 2 8.5c0 2.3 1.5 4.05 3 5.5l7 7Z" />
      </svg>
      Thich <span v-if="likes > 0">({{ likes }})</span>
    </button>

    <button
      type="button"
      class="flex items-center gap-2 rounded-full px-3 py-1.5 text-sm font-medium transition-colors"
      :class="followClass"
      :disabled="pendingAction === 'follow'"
      @click="toggleInteraction('follow')"
    >
      <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2" />
        <circle cx="9" cy="7" r="4" />
        <line x1="19" x2="19" y1="8" y2="14" />
        <line x1="22" x2="16" y1="11" y2="11" />
      </svg>
      {{ followed ? "Dang theo doi" : "Theo doi" }} <span v-if="follows > 0">({{ follows }})</span>
    </button>

    <ReportDialog :target-type="targetType" :target-document-id="targetDocumentId" />

    <button
      type="button"
      class="flex items-center gap-2 rounded-full px-3 py-1.5 text-sm font-medium transition-colors"
      :class="shareClass"
      @click="handleShare"
    >
      {{ copied ? "Da sao chep!" : "Chia se" }}
    </button>
  </div>
</template>

<script setup lang="ts">
const props = defineProps<{
  targetType: string;
  targetDocumentId: string;
}>();

const auth = useAuth();
const theme = useTheme();
const liked = ref(false);
const likes = ref(0);
const followed = ref(false);
const follows = ref(0);
const copied = ref(false);
const pendingAction = ref<"like" | "follow" | null>(null);
const wrapperClass = computed(() => (theme.isDark.value ? "mt-8 flex flex-wrap gap-3 border-b border-t border-zinc-800 py-4" : "mt-8 flex flex-wrap gap-3 border-b border-t border-zinc-200 py-4"));
const likeClass = computed(() => {
  if (liked.value) {
    return theme.isDark.value ? "bg-red-900/20 text-red-400" : "bg-red-50 text-red-600";
  }
  return theme.isDark.value ? "text-zinc-400 hover:bg-red-500/10 hover:text-red-300" : "text-zinc-600 hover:bg-red-50 hover:text-red-600";
});
const followClass = computed(() => {
  if (followed.value) {
    return theme.isDark.value ? "bg-blue-900/20 text-blue-400" : "bg-blue-50 text-blue-600";
  }
  return theme.isDark.value ? "text-zinc-400 hover:bg-blue-500/10 hover:text-blue-300" : "text-zinc-600 hover:bg-blue-50 hover:text-blue-600";
});
const shareClass = computed(() => {
  if (copied.value) {
    return theme.isDark.value ? "bg-green-900/20 text-green-400" : "bg-green-50 text-green-600";
  }
  return theme.isDark.value ? "text-zinc-400 hover:bg-zinc-800 hover:text-zinc-100" : "text-zinc-600 hover:bg-zinc-100 hover:text-zinc-900";
});

async function loadState() {
  if (!auth.isHydrated.value) return;
  if (!auth.isLoggedIn.value) {
    liked.value = false;
    followed.value = false;
    likes.value = 0;
    follows.value = 0;
    return;
  }
  try {
    const response = await auth.authorizedFetch(`/api/interaction-proxy?targetType=${encodeURIComponent(props.targetType)}&targetDocumentId=${encodeURIComponent(props.targetDocumentId)}`, { cache: "no-store" });
    if (!response.ok) return;
    const payload = await response.json();
    likes.value = payload.likesCount ?? 0;
    follows.value = payload.followsCount ?? 0;
    liked.value = !!payload.liked;
    followed.value = !!payload.followed;
  } catch {
    // ignore
  }
}

watchEffect(() => {
  if (!auth.isHydrated.value) return;
  void loadState();
});

async function toggleInteraction(actionType: "like" | "follow") {
  if (!auth.isLoggedIn.value) {
    auth.openLoginModal();
    return;
  }
  if (pendingAction.value === actionType) return;
  pendingAction.value = actionType;
  const response = await auth.authorizedFetch("/api/interaction-proxy", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      actionType,
      targetType: props.targetType,
      targetDocumentId: props.targetDocumentId,
    }),
  });
  try {
    if (!response.ok) return;
    const payload = await response.json().catch(() => ({}));
    const active = !!payload?.toggled;
    if (actionType === "like") {
      liked.value = active;
      likes.value = active ? likes.value + 1 : Math.max(0, likes.value - 1);
      return;
    }
    followed.value = active;
    follows.value = active ? follows.value + 1 : Math.max(0, follows.value - 1);
  } finally {
    pendingAction.value = null;
  }
}

async function handleShare() {
  try {
    await navigator.clipboard.writeText(window.location.href);
    copied.value = true;
    window.setTimeout(() => {
      copied.value = false;
    }, 2500);
  } catch {
    // ignore
  }
}
</script>
