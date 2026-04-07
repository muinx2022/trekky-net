<template>
  <div>
    <div class="py-1 text-gray-800">
      <div class="mb-1 flex items-start justify-between gap-3">
        <div class="flex items-center gap-2">
          <img
            v-if="authorAvatarUrl"
            :src="authorAvatarUrl"
            :alt="comment.authorName ? `${comment.authorName} avatar` : 'User avatar'"
            width="28"
            height="28"
            class="h-7 w-7 rounded-full bg-gray-200 object-cover ring-1 ring-gray-300"
          />
          <div v-else class="flex h-7 w-7 items-center justify-center rounded-full bg-gray-200 text-xs font-bold uppercase text-blue-600 ring-1 ring-gray-300">
            {{ comment.authorName?.[0] ?? "?" }}
          </div>
          <p class="text-sm font-semibold text-gray-900">{{ comment.authorName }}</p>
        </div>
        <span class="text-xs text-gray-500">{{ formatRelativeCommentTime(comment.createdAt) }}</span>
      </div>

      <RichTextContent :html="comment.content" mode="comment" class-name="richtext-content pl-9 text-gray-700" />

      <div class="mt-2 flex gap-3 pl-9">
        <button
          type="button"
          class="flex items-center gap-1 text-xs font-medium transition-colors"
          :class="liked ? 'text-red-500' : 'text-gray-500 hover:text-red-500'"
          :disabled="liking"
          @click="emit('like', comment.documentId)"
        >
          <svg xmlns="http://www.w3.org/2000/svg" width="13" height="13" viewBox="0 0 24 24" :fill="liked ? 'currentColor' : 'none'" stroke="currentColor" stroke-width="2">
            <path d="M19 14c1.49-1.46 3-3.21 3-5.5A5.5 5.5 0 0 0 16.5 3c-1.76 0-3 .5-4.5 2-1.5-1.5-2.74-2-4.5-2A5.5 5.5 0 0 0 2 8.5c0 2.3 1.5 4.05 3 5.5l7 7Z" />
          </svg>
          Thich
        </button>

        <button type="button" class="text-xs font-medium text-gray-500 transition-colors hover:text-blue-600" @click="handleReplyToggle">
          {{ replies.length > 0 ? `Tra loi (${replies.length})` : "Tra loi" }}
        </button>
      </div>
    </div>

    <div v-if="replies.length > 0" :class="replyListClass">
      <GenericCommentsItem
        v-for="reply in replies"
        :key="reply.documentId"
        :comment="reply"
        :replies-by-parent="repliesByParent"
        :replying-to="replyingTo"
        :comment-likes="commentLikes"
        :liking-ids="likingIds"
        @like="emit('like', $event)"
        @reply-toggle="emit('reply-toggle', $event)"
        @reply-cancel="emit('reply-cancel')"
        @reply-submit="emit('reply-submit', $event)"
      />
    </div>

    <div v-if="replyingTo === comment.documentId" :class="replyEditorWrapperClass">
      <div :class="replyEditorShellClass">
        <p :class="replyHintClass">Tra loi {{ comment.authorName }}</p>

        <div :class="replyEditorFrameClass">
          <TiptapEditor v-model="replyHtml" :show-toolbar="showToolbar" compact :allow-media="false" :theme="editorTheme" />
        </div>

        <p v-if="replyError" class="mb-2 text-xs text-red-500">{{ replyError }}</p>

        <div class="flex items-center justify-between">
          <button type="button" class="text-xs font-medium text-blue-600 transition-colors hover:text-blue-700" @click="showToolbar = !showToolbar">
            {{ showToolbar ? "An dinh dang" : "Hien thi dinh dang" }}
          </button>

          <div class="flex gap-2">
            <button type="button" :class="cancelButtonClass" @click="emit('reply-cancel')">
              Huy
            </button>
            <button
              type="button"
              class="flex items-center gap-1 rounded-lg bg-blue-600 px-3 py-1.5 text-xs font-medium text-white hover:bg-blue-700 disabled:cursor-not-allowed disabled:opacity-50"
              :disabled="replying || !isMeaningfulHtml(replyHtml)"
              @click="submitReply"
            >
              <svg v-if="replying" class="animate-spin" xmlns="http://www.w3.org/2000/svg" width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M21 12a9 9 0 1 1-6.219-8.56" />
              </svg>
              Gui
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import type { Comment } from "~~/shared/types";

const props = defineProps<{
  comment: Comment;
  repliesByParent: Record<string, Comment[]>;
  replyingTo: string | null;
  commentLikes: Record<string, boolean>;
  likingIds: string[];
}>();

const emit = defineEmits<{
  like: [documentId: string];
  replyToggle: [documentId: string];
  replyCancel: [];
  replySubmit: [payload: { parentDocumentId: string; html: string; done: (error?: string) => void }];
}>();

const auth = useAuth();
const theme = useTheme();
const replyHtml = ref("");
const showToolbar = ref(false);
const replyError = ref("");
const replying = ref(false);

const replies = computed(() => props.repliesByParent[props.comment.documentId] ?? []);
const liked = computed(() => props.commentLikes[props.comment.documentId] ?? false);
const liking = computed(() => props.likingIds.includes(props.comment.documentId));
const authorAvatarUrl = computed(() => props.comment.authorAvatarUrl ?? "");
const editorTheme = computed(() => (theme.isDark.value ? "comment-dark" : "default"));
const replyListClass = computed(() => (theme.isDark.value ? "ml-3 mt-2 space-y-2 border-l border-slate-700 pl-5" : "ml-3 mt-2 space-y-2 border-l border-gray-200 pl-5"));
const replyEditorWrapperClass = computed(() => (theme.isDark.value ? "ml-3 mt-2 border-l border-slate-700 pl-5" : "ml-3 mt-2 border-l border-gray-200 pl-5"));
const replyEditorShellClass = computed(() => (theme.isDark.value ? "rounded-2xl border border-slate-800 bg-slate-900 p-3 text-slate-100 shadow-sm" : "rounded-2xl bg-zinc-50 p-3 text-zinc-900 shadow-sm"));
const replyHintClass = computed(() => (theme.isDark.value ? "mb-2 text-xs text-slate-400" : "mb-2 text-xs text-zinc-500"));
const replyEditorFrameClass = computed(() => (theme.isDark.value ? "mb-3 rounded-xl bg-slate-900 p-2 transition-all focus-within:ring-2 focus-within:ring-sky-500/15" : "mb-3 rounded-xl bg-white p-2 transition-all focus-within:ring-2 focus-within:ring-blue-500/10"));
const cancelButtonClass = computed(() => (theme.isDark.value ? "rounded-lg px-3 py-1.5 text-xs font-medium text-slate-300 transition-colors hover:bg-slate-800" : "rounded-lg px-3 py-1.5 text-xs font-medium text-zinc-600 transition-colors hover:bg-zinc-100"));

function isMeaningfulHtml(html: string) {
  const trimmed = html.trim();
  return !!trimmed && trimmed !== "<p></p>";
}

function formatRelativeCommentTime(dateStr: string) {
  const diff = Date.now() - new Date(dateStr).getTime();
  const mins = Math.floor(diff / 60000);
  const hours = Math.floor(mins / 60);
  const days = Math.floor(hours / 24);
  if (mins < 1) return "vua xong";
  if (mins < 60) return `${mins} phut truoc`;
  if (hours < 24) return `${hours} gio truoc`;
  return `${days} ngay truoc`;
}

function handleReplyToggle() {
  if (!auth.isLoggedIn.value) {
    auth.openLoginModal();
    return;
  }
  emit("replyToggle", props.comment.documentId);
}

function submitReply() {
  if (!isMeaningfulHtml(replyHtml.value)) return;
  replying.value = true;
  replyError.value = "";
  emit("replySubmit", {
    parentDocumentId: props.comment.documentId,
    html: replyHtml.value,
    done(error?: string) {
      replying.value = false;
      if (error) {
        replyError.value = error;
        return;
      }
      replyHtml.value = "";
      showToolbar.value = false;
    },
  });
}
</script>
