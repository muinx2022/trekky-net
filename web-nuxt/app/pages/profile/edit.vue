<template>
  <section class="max-w-3xl space-y-5">
    <div class="overflow-hidden rounded-[2rem] border border-slate-200 bg-[linear-gradient(135deg,#f8fafc_0%,#e0f2fe_45%,#fff7ed_100%)] shadow-sm dark:border-slate-700 dark:bg-[linear-gradient(135deg,#0f172a_0%,#0b253a_45%,#172033_100%)]">
      <div class="px-6 py-8 sm:px-8 lg:px-10">
        <span class="inline-flex w-fit items-center rounded-full border border-white/70 bg-white/80 px-3 py-1 text-xs font-semibold uppercase tracking-[0.24em] text-sky-700 shadow-sm backdrop-blur dark:border-slate-500/60 dark:bg-slate-900/60 dark:text-sky-200">
          Hồ sơ
        </span>
        <div class="mt-3 space-y-2">
          <h1 class="text-3xl font-semibold tracking-tight text-slate-900 dark:text-slate-50 sm:text-4xl">Chỉnh sửa hồ sơ</h1>
          <p class="max-w-2xl text-sm leading-6 text-slate-600 dark:text-slate-300 sm:text-base">
            Cập nhật mô tả ngắn, ảnh đại diện và những thông tin giúp trang cá nhân của bạn nhìn gọn gàng hơn.
          </p>
        </div>
      </div>
    </div>

    <div class="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
      <div v-if="!auth.isLoggedIn.value">
        <p class="text-sm text-slate-600">Bạn cần đăng nhập để cập nhật hồ sơ.</p>
        <button class="mt-3 rounded-xl bg-sky-600 px-4 py-2 text-sm font-medium text-white hover:bg-sky-700" @click="auth.openLoginModal()">Đăng nhập</button>
      </div>

      <form v-else class="space-y-4" @submit.prevent="submit">
        <div class="flex flex-col gap-4 sm:flex-row sm:items-center">
          <img v-if="avatarPreviewUrl" :src="avatarPreviewUrl" alt="avatar" class="h-20 w-20 rounded-full object-cover bg-slate-300" />
          <div v-else class="flex h-20 w-20 items-center justify-center rounded-full bg-slate-300 text-2xl font-semibold text-slate-700">
            {{ auth.user.value?.username?.slice(0, 1).toUpperCase() }}
          </div>
          <div class="space-y-3">
            <input ref="fileInputRef" type="file" accept="image/*" @change="handleFileChange" />
            <div class="flex flex-wrap gap-2">
              <button
                v-if="avatarFile"
                type="button"
                class="rounded-xl border border-slate-300 px-3 py-2 text-sm font-medium text-slate-700 hover:bg-slate-50"
                @click="clearSelectedAvatar"
              >
                Bỏ file đã chọn
              </button>
              <button
                v-if="showRemoveAvatarButton"
                type="button"
                class="rounded-xl border border-rose-200 px-3 py-2 text-sm font-medium text-rose-600 hover:bg-rose-50"
                @click="removeUploadedAvatar"
              >
                Xóa avatar
              </button>
            </div>
            <p class="text-xs text-slate-500">
              {{ avatarFile ? "Ảnh xem trước đang được hiển thị từ file bạn vừa chọn." : "Chọn ảnh đại diện mới, hoặc xóa avatar hiện tại nếu không muốn hiển ảnh." }}
            </p>
          </div>
        </div>

        <label class="block text-sm">
          <span class="mb-1 block text-slate-700">Bio</span>
          <textarea v-model="bio" rows="5" class="w-full rounded-xl border border-slate-300 px-3 py-2 outline-none focus:border-sky-500" />
        </label>

        <p v-if="message" class="rounded-xl px-3 py-2 text-sm" :class="messageClass">{{ message }}</p>

        <button
          type="submit"
          class="rounded-xl bg-sky-600 px-4 py-2 text-sm font-medium text-white hover:bg-sky-700 disabled:cursor-not-allowed disabled:bg-slate-300"
          :disabled="pending"
        >
          {{ pending ? "Đang lưu..." : "Cập nhật hồ sơ" }}
        </button>
      </form>
    </div>
  </section>
</template>

<script setup lang="ts">
const auth = useAuth();
const bio = ref("");
const avatarFile = ref<File | null>(null);
const avatarPreviewUrl = ref("");
const pending = ref(false);
const message = ref("");
const messageClass = ref("bg-emerald-50 text-emerald-700");
const fileInputRef = ref<HTMLInputElement | null>(null);

const showRemoveAvatarButton = computed(() => !!auth.user.value?.avatarUrl && !avatarFile.value);

watchEffect(() => {
  bio.value = auth.user.value?.bio ?? "";
});

watch(
  () => auth.user.value?.avatarUrl,
  (avatarUrl) => {
    if (!avatarFile.value) avatarPreviewUrl.value = avatarUrl ?? "";
  },
  { immediate: true },
);

onBeforeUnmount(() => {
  revokePreviewUrl();
});

function revokePreviewUrl() {
  if (!avatarPreviewUrl.value.startsWith("blob:")) return;
  URL.revokeObjectURL(avatarPreviewUrl.value);
}

function handleFileChange(event: Event) {
  const input = event.target as HTMLInputElement;
  const nextFile = input.files?.[0] ?? null;
  avatarFile.value = nextFile;
  revokePreviewUrl();
  avatarPreviewUrl.value = nextFile ? URL.createObjectURL(nextFile) : auth.user.value?.avatarUrl ?? "";
}

function clearSelectedAvatar() {
  avatarFile.value = null;
  revokePreviewUrl();
  avatarPreviewUrl.value = auth.user.value?.avatarUrl ?? "";
  if (fileInputRef.value) fileInputRef.value.value = "";
}

async function removeUploadedAvatar() {
  pending.value = true;
  const error = await auth.updateProfile({ bio: bio.value, avatarFile: null, removeAvatar: true });
  pending.value = false;
  if (error) {
    messageClass.value = "bg-rose-50 text-rose-700";
    message.value = error;
    return;
  }
  clearSelectedAvatar();
  avatarPreviewUrl.value = "";
  messageClass.value = "bg-emerald-50 text-emerald-700";
  message.value = "Đã xóa avatar.";
}

async function submit() {
  pending.value = true;
  const error = await auth.updateProfile({ bio: bio.value, avatarFile: avatarFile.value });
  pending.value = false;
  if (error) {
    messageClass.value = "bg-rose-50 text-rose-700";
    message.value = error;
    return;
  }
  clearSelectedAvatar();
  messageClass.value = "bg-emerald-50 text-emerald-700";
  message.value = "Đã cập nhật hồ sơ.";
}
</script>
