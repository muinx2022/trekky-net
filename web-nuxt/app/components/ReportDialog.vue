<template>
  <div>
    <button
      type="button"
      :disabled="alreadyReported"
      :title="alreadyReported ? 'Ban da bao cao noi dung nay' : 'Bao cao noi dung'"
      :class="buttonClass"
      @click="handleOpen"
    >
      <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <path d="M4 15s1-1 4-1 5 2 8 2 4-1 4-1V3s-1 1-4 1-5-2-8-2-4 1-4 1z" />
        <line x1="4" x2="4" y1="22" y2="15" />
      </svg>
      {{ alreadyReported ? "Da bao cao" : "Bao cao" }}
    </button>

    <Teleport to="body">
      <div v-if="isOpen" class="fixed inset-0 z-[110] flex items-center justify-center p-4">
        <button type="button" class="absolute inset-0 bg-black/50 backdrop-blur-sm" aria-label="Dong bao cao" @click="handleClose" />

        <div :class="dialogClass">
          <div class="flex items-start justify-between">
            <div>
              <h2 :class="titleClass">Bao cao bai viet</h2>
              <p :class="subtitleClass">Noi dung vi pham se duoc doi ngu kiem duyet xem xet.</p>
            </div>
            <button type="button" :class="closeButtonClass" aria-label="Dong bao cao" @click="handleClose">
              <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
                <path d="M18 6 6 18" />
                <path d="m6 6 12 12" />
              </svg>
            </button>
          </div>

          <div v-if="status === 'success'" class="flex flex-col items-center gap-3 py-6 text-green-600 dark:text-green-400">
            <svg xmlns="http://www.w3.org/2000/svg" width="36" height="36" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14" />
              <path d="m9 11 3 3L22 4" />
            </svg>
            <p class="text-sm font-medium">Bao cao da duoc gui. Cam on ban.</p>
          </div>

          <div v-else class="flex flex-col gap-5">
            <div class="flex flex-col gap-2">
              <p :class="labelClass">Ly do bao cao <span class="text-red-500">*</span></p>
              <div class="grid grid-cols-2 gap-2">
                <button
                  v-for="item in REPORT_CATEGORIES"
                  :key="item.value"
                  type="button"
                  :class="categoryButtonClass(item.value)"
                  @click="category = item.value"
                >
                  {{ item.label }}
                </button>
              </div>
            </div>

            <div class="flex flex-col gap-1.5">
              <label for="report-details" :class="labelClass">
                Chi tiet them <span :class="hintClass">(tuy chon)</span>
              </label>
              <textarea
                id="report-details"
                v-model="reason"
                rows="3"
                maxlength="500"
                :class="textareaClass"
                placeholder="Mo ta ngan gon van de ban phat hien..."
              />
              <div :class="counterClass">{{ reason.length }}/500</div>
            </div>

            <p v-if="status === 'error'" class="text-sm text-red-500">Co loi xay ra, vui long thu lai.</p>

            <div class="flex justify-end gap-2 pt-1">
              <button type="button" :class="cancelClass" @click="handleClose">Huy</button>
              <button type="button" :disabled="!category || status === 'loading'" class="rounded-full bg-gray-500 px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-gray-600 disabled:cursor-not-allowed disabled:opacity-50" @click="submitReport">
                {{ status === "loading" ? "Dang gui..." : "Gui bao cao" }}
              </button>
            </div>
          </div>
        </div>
      </div>
    </Teleport>
  </div>
</template>

<script setup lang="ts">
const props = defineProps<{
  targetType: string;
  targetDocumentId: string;
}>();

const REPORT_CATEGORIES = [
  { value: "incorrect_info", label: "Thong tin sai" },
  { value: "spam", label: "Spam / Quang cao" },
  { value: "harassment", label: "Quay roi" },
  { value: "inappropriate", label: "Noi dung khong phu hop" },
  { value: "copyright", label: "Ban quyen" },
  { value: "other", label: "Ly do khac" },
];

const auth = useAuth();
const theme = useTheme();
const isOpen = ref(false);
const category = ref("");
const reason = ref("");
const status = ref<"idle" | "loading" | "success" | "error">("idle");
const serverReported = ref(false);
const checkedReported = ref(false);

const reportKey = computed(() => `reported:${props.targetType}:${props.targetDocumentId}`);
const localReported = computed(() => {
  if (!import.meta.client) return false;
  try {
    return Boolean(localStorage.getItem(reportKey.value));
  } catch {
    return false;
  }
});
const alreadyReported = computed(() => localReported.value || serverReported.value);

const buttonClass = computed(() => {
  if (alreadyReported.value) {
    return theme.isDark.value
      ? "flex items-center gap-2 rounded-full px-3 py-1.5 text-sm font-medium text-slate-600 transition-colors cursor-not-allowed"
      : "flex items-center gap-2 rounded-full px-3 py-1.5 text-sm font-medium text-zinc-300 transition-colors cursor-not-allowed";
  }
  return theme.isDark.value
    ? "flex items-center gap-2 rounded-full px-3 py-1.5 text-sm font-medium text-zinc-400 transition-colors hover:text-red-400 hover:bg-red-900/20"
    : "flex items-center gap-2 rounded-full px-3 py-1.5 text-sm font-medium text-zinc-500 transition-colors hover:text-red-600 hover:bg-red-50";
});

const dialogClass = computed(() =>
  theme.isDark.value
    ? "relative flex w-full max-w-md flex-col gap-5 rounded-2xl border border-zinc-800 bg-zinc-950 p-6 shadow-2xl"
    : "relative flex w-full max-w-md flex-col gap-5 rounded-2xl border border-zinc-200 bg-white p-6 shadow-2xl",
);
const titleClass = computed(() => (theme.isDark.value ? "text-base font-bold text-zinc-50" : "text-base font-bold text-zinc-900"));
const subtitleClass = computed(() => (theme.isDark.value ? "mt-0.5 text-sm text-zinc-400" : "mt-0.5 text-sm text-zinc-500"));
const closeButtonClass = computed(() =>
  theme.isDark.value
    ? "rounded-full p-1.5 text-zinc-400 transition-colors hover:bg-zinc-800 hover:text-zinc-200"
    : "rounded-full p-1.5 text-zinc-400 transition-colors hover:bg-zinc-100 hover:text-zinc-700",
);
const labelClass = computed(() => (theme.isDark.value ? "text-sm font-medium text-zinc-300" : "text-sm font-medium text-zinc-700"));
const hintClass = computed(() => (theme.isDark.value ? "font-normal text-zinc-500" : "font-normal text-zinc-400"));
const textareaClass = computed(() =>
  theme.isDark.value
    ? "w-full resize-none rounded-lg border border-zinc-700 bg-zinc-900 p-3 text-sm text-zinc-100 placeholder-zinc-500 transition focus:outline-none focus:ring-2 focus:ring-blue-400"
    : "w-full resize-none rounded-lg border border-zinc-200 bg-zinc-50 p-3 text-sm text-zinc-900 placeholder-zinc-400 transition focus:outline-none focus:ring-2 focus:ring-blue-500",
);
const counterClass = computed(() => (theme.isDark.value ? "text-right text-xs text-zinc-500" : "text-right text-xs text-zinc-400"));
const cancelClass = computed(() =>
  theme.isDark.value
    ? "rounded-lg px-4 py-2 text-sm font-medium text-zinc-400 transition-colors hover:bg-zinc-800"
    : "rounded-lg px-4 py-2 text-sm font-medium text-zinc-600 transition-colors hover:bg-zinc-100",
);

function categoryButtonClass(value: string) {
  const active = category.value === value;
  if (active) {
    return theme.isDark.value
      ? "rounded-lg border border-blue-500 bg-blue-900/20 px-3 py-2 text-left text-sm font-medium text-blue-300 transition-colors"
      : "rounded-lg border border-blue-500 bg-blue-50 px-3 py-2 text-left text-sm font-medium text-blue-700 transition-colors";
  }
  return theme.isDark.value
    ? "rounded-lg border border-zinc-700 px-3 py-2 text-left text-sm text-zinc-400 transition-colors hover:border-zinc-500 hover:bg-zinc-900"
    : "rounded-lg border border-zinc-200 px-3 py-2 text-left text-sm text-zinc-600 transition-colors hover:border-zinc-400 hover:bg-zinc-50";
}

function resetDialogState() {
  category.value = "";
  reason.value = "";
  status.value = "idle";
}

async function loadReportedState() {
  if (!auth.isHydrated.value) return;
  if (!auth.isLoggedIn.value) {
    serverReported.value = false;
    checkedReported.value = true;
    return;
  }

  try {
    const response = await auth.authorizedFetch(`/api/report-proxy?targetType=${encodeURIComponent(props.targetType)}&targetDocumentId=${encodeURIComponent(props.targetDocumentId)}`, {
      cache: "no-store",
    });
    if (!response.ok) {
      checkedReported.value = true;
      return;
    }
    const payload = await response.json().catch(() => ({}));
    serverReported.value = !!payload?.data?.reported;
    if (serverReported.value && import.meta.client) {
      localStorage.setItem(reportKey.value, "1");
    }
  } catch {
    // ignore
  } finally {
    checkedReported.value = true;
  }
}

watch(
  () => [props.targetType, props.targetDocumentId],
  () => {
    checkedReported.value = false;
    serverReported.value = false;
  },
  { immediate: true },
);

watchEffect(() => {
  if (!auth.isHydrated.value || checkedReported.value) return;
  void loadReportedState();
});

function handleOpen() {
  if (!auth.isLoggedIn.value) {
    auth.openLoginModal();
    return;
  }
  if (alreadyReported.value) return;
  resetDialogState();
  isOpen.value = true;
}

function handleClose() {
  isOpen.value = false;
  resetDialogState();
}

async function submitReport() {
  if (!auth.isLoggedIn.value) {
    auth.openLoginModal();
    return;
  }
  if (!category.value) return;

  status.value = "loading";
  const categoryLabel = REPORT_CATEGORIES.find((item) => item.value === category.value)?.label ?? category.value;
  const fullReason = reason.value.trim() ? `[${categoryLabel}] ${reason.value.trim()}` : `[${categoryLabel}]`;

  const response = await auth.authorizedFetch("/api/report-proxy", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      targetType: props.targetType,
      targetDocumentId: props.targetDocumentId,
      reason: fullReason,
    }),
  }).catch(() => null);

  if (!response) {
    status.value = "error";
    return;
  }

  const payload = await response.json().catch(() => ({}));
  if (payload?.data?.alreadyReported) {
    serverReported.value = true;
    if (import.meta.client) localStorage.setItem(reportKey.value, "1");
    handleClose();
    return;
  }

  if (!response.ok) {
    status.value = "error";
    return;
  }

  status.value = "success";
  serverReported.value = true;
  if (import.meta.client) localStorage.setItem(reportKey.value, "1");
  window.setTimeout(() => {
    handleClose();
  }, 1800);
}
</script>
