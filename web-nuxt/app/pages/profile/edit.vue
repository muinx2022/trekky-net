<template>
  <div class="max-w-2xl">
    <div class="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
      <h1 class="text-2xl font-semibold text-slate-900">Chinh sua ho so</h1>
      <p class="mt-1 text-sm text-slate-500">Cap nhat mo ta ngan va anh dai dien cua ban.</p>

      <div v-if="!auth.isLoggedIn.value" class="mt-4">
        <p class="text-sm text-slate-600">Ban can dang nhap de cap nhat ho so.</p>
        <button class="mt-3 rounded-xl bg-sky-600 px-4 py-2 text-sm font-medium text-white hover:bg-sky-700" @click="auth.openLoginModal()">Dang nhap</button>
      </div>

      <form v-else class="mt-5 space-y-4" @submit.prevent="submit">
        <div class="flex items-center gap-4">
          <img v-if="auth.user.value?.avatarUrl" :src="auth.user.value.avatarUrl" alt="avatar" class="h-16 w-16 rounded-full object-cover bg-slate-300" />
          <div v-else class="flex h-16 w-16 items-center justify-center rounded-full bg-slate-300 text-xl font-semibold text-slate-700">
            {{ auth.user.value?.username?.slice(0, 1).toUpperCase() }}
          </div>
          <input type="file" accept="image/*" @change="handleFileChange" />
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
          {{ pending ? "Dang luu..." : "Cap nhat ho so" }}
        </button>
      </form>
    </div>
  </div>
</template>

<script setup lang="ts">
const auth = useAuth();
const bio = ref("");
const avatarFile = ref<File | null>(null);
const pending = ref(false);
const message = ref("");
const messageClass = ref("bg-emerald-50 text-emerald-700");

watchEffect(() => {
  bio.value = auth.user.value?.bio ?? "";
});

function handleFileChange(event: Event) {
  const input = event.target as HTMLInputElement;
  avatarFile.value = input.files?.[0] ?? null;
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
  messageClass.value = "bg-emerald-50 text-emerald-700";
  message.value = "Da cap nhat ho so.";
}
</script>
