<template>
  <div class="space-y-6">
    <div v-if="successMsg" class="flex items-center gap-2 rounded-lg border border-green-200 bg-green-50 px-4 py-3 text-sm text-green-700">
      Đã gửi bình luận.
    </div>

    <div v-if="errorMsg" class="flex items-center gap-2 rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-600">
      {{ errorMsg }}
    </div>

    <button
      v-if="!isJoined"
      type="button"
      :class="joinBoxClass"
      class="comment-join-box"
      @click="handleJoinClick"
    >
      <svg class="comment-join-icon" xmlns="http://www.w3.org/2000/svg" width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" /></svg>
      <p :class="joinTextClass" class="comment-join-text">{{ auth.isLoggedIn.value ? "Nhấn để tham gia thảo luận..." : "Đăng nhập để bình luận..." }}</p>
    </button>

    <div v-else :class="editorShellClass" class="comment-editor-shell">
      <div :class="editorFrameClass" class="comment-editor-frame">
        <TiptapEditor v-model="commentHtml" :show-toolbar="showToolbar" compact :allow-media="false" :theme="editorTheme" />
      </div>

      <div class="flex items-center justify-between">
        <button type="button" class="text-xs font-medium text-blue-600 transition-colors hover:text-blue-700" @click="showToolbar = !showToolbar">
          {{ showToolbar ? "Ẩn định dạng" : "Hiển thị định dạng" }}
        </button>

        <div class="flex gap-2">
          <button type="button" :class="cancelButtonClass" @click="isJoined = false">
            Hủy
          </button>
          <button
            type="button"
            class="flex items-center gap-2 rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700 disabled:cursor-not-allowed disabled:opacity-50"
            :disabled="submitting || !isMeaningfulHtml(commentHtml)"
            @click="handlePostComment"
          >
            <svg v-if="submitting" class="animate-spin" xmlns="http://www.w3.org/2000/svg" width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M21 12a9 9 0 1 1-6.219-8.56" />
            </svg>
            Bình luận
          </button>
        </div>
      </div>
    </div>

    <div class="mt-8 space-y-4">
      <GenericCommentsItem
        v-for="comment in topLevelComments"
        :key="comment.documentId"
        :comment="comment"
        :replies-by-parent="repliesByParent"
        :replying-to="replyingTo"
        :comment-likes="commentLikes"
        :liking-ids="Array.from(likingIds)"
        @like="handleLikeComment"
        @reply-toggle="handleReplyToggle"
        @reply-cancel="replyingTo = null"
        @reply-submit="handleReplySubmit"
      />

      <div v-if="topLevelComments.length === 0" :class="emptyStateClass">
        Chưa có bình luận nào. Hãy là người đầu tiên!
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import type { Comment } from "../../shared/types";

const props = defineProps<{
  targetType: "post" | "page" | "product" | "other";
  targetDocumentId: string;
  initialComments: Comment[];
}>();

const auth = useAuth();
const theme = useTheme();
const comments = ref<Comment[]>([]);
const isJoined = ref(false);
const commentHtml = ref("");
const showToolbar = ref(false);
const submitting = ref(false);
const successMsg = ref("");
const errorMsg = ref("");
const replyingTo = ref<string | null>(null);
const commentLikes = ref<Record<string, boolean>>({});
const likingIds = ref<Set<string>>(new Set());
const editorTheme = computed(() => (theme.isDark.value ? "comment-dark" : "default"));
const joinBoxClass = computed(() =>
  theme.isDark.value
    ? "flex w-full cursor-pointer items-center gap-3 rounded-2xl border border-dashed border-slate-700 bg-gradient-to-r from-slate-900 to-slate-800 px-4 py-3 text-left text-slate-200 shadow-sm transition-colors hover:border-sky-500 hover:from-slate-800 hover:to-slate-900"
    : "flex w-full cursor-pointer items-center gap-3 rounded-2xl border border-dashed border-zinc-300 bg-gradient-to-r from-white to-zinc-50 px-4 py-3 text-left text-zinc-700 shadow-sm transition-colors hover:border-blue-400 hover:from-blue-50 hover:to-white",
);
const joinTextClass = computed(() => (theme.isDark.value ? "text-sm text-slate-400" : "text-sm text-zinc-500"));
const editorShellClass = computed(() => (theme.isDark.value ? "rounded-2xl border border-slate-800 bg-slate-900 p-4 text-slate-100 shadow-sm" : "rounded-2xl bg-zinc-50 p-4 text-zinc-900 shadow-sm"));
const editorFrameClass = computed(() => (theme.isDark.value ? "mb-4 rounded-xl bg-slate-900 p-3 transition-all focus-within:ring-2 focus-within:ring-sky-500/15" : "mb-4 rounded-xl bg-white p-3 transition-all focus-within:ring-2 focus-within:ring-blue-500/10"));
const cancelButtonClass = computed(() => (theme.isDark.value ? "rounded-lg px-4 py-2 text-sm font-medium text-slate-300 transition-colors hover:bg-slate-800" : "rounded-lg px-4 py-2 text-sm font-medium text-zinc-600 transition-colors hover:bg-zinc-100"));
const emptyStateClass = computed(() => (theme.isDark.value ? "rounded-2xl border border-slate-700 bg-slate-900 px-4 py-8 text-center text-sm text-slate-400" : "rounded-2xl border border-zinc-200 bg-zinc-50 px-4 py-8 text-center text-sm text-zinc-500"));

watch(
  () => props.initialComments,
  (value) => {
    comments.value = [...value];
  },
  { immediate: true },
);

const topLevelComments = computed(() =>
  comments.value
    .filter((comment) => !comment.parent?.documentId)
    .sort((a, b) => new Date(b.createdAt).getTime() - new Date(a.createdAt).getTime()),
);

const repliesByParent = computed(() => {
  const map: Record<string, Comment[]> = {};
  comments.value.forEach((comment) => {
    const parentId = comment.parent?.documentId;
    if (!parentId) return;
    map[parentId] ??= [];
    map[parentId].push(comment);
  });
  Object.keys(map).forEach((key) => map[key].sort((a, b) => new Date(a.createdAt).getTime() - new Date(b.createdAt).getTime()));
  return map;
});

function isMeaningfulHtml(html: string) {
  const trimmed = html.trim();
  return !!trimmed && trimmed !== "<p></p>";
}

async function postComment(body: object) {
  try {
    const response = await auth.authorizedFetch("/api/comment-proxy", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });
    if (!response.ok) {
      const payload = await response.json().catch(() => ({}));
      return { ok: false, error: payload?.error || "Gửi bình luận thất bại." };
    }
    return { ok: true, data: (await response.json()).data as Comment };
  } catch {
    return { ok: false, error: "Không thể kết nối. Vui lòng thử lại." };
  }
}

function handleJoinClick() {
  if (!auth.isLoggedIn.value) {
    auth.openLoginModal();
    return;
  }
  replyingTo.value = null;
  isJoined.value = true;
}

async function handlePostComment() {
  if (!auth.user.value) {
    auth.openLoginModal();
    return;
  }
  if (!isMeaningfulHtml(commentHtml.value)) return;
  submitting.value = true;
  errorMsg.value = "";
  const result = await postComment({
    authorName: auth.user.value.username,
    authorEmail: auth.user.value.email,
    content: commentHtml.value.trim(),
    targetType: props.targetType,
    targetDocumentId: props.targetDocumentId,
  });
  submitting.value = false;
  if (!result.ok || !result.data) {
    errorMsg.value = result.error ?? "Lỗi không xác định.";
    return;
  }
  comments.value = [result.data, ...comments.value];
  isJoined.value = false;
  commentHtml.value = "";
  showToolbar.value = false;
  successMsg.value = "Cảm ơn bạn đã tham gia bình luận!";
  window.setTimeout(() => {
    successMsg.value = "";
  }, 5000);
}

async function handleLikeComment(commentDocumentId: string) {
  if (!auth.isLoggedIn.value) {
    auth.openLoginModal();
    return;
  }
  if (likingIds.value.has(commentDocumentId)) return;
  const previous = commentLikes.value[commentDocumentId] ?? false;
  commentLikes.value = { ...commentLikes.value, [commentDocumentId]: !previous };
  likingIds.value = new Set([...likingIds.value, commentDocumentId]);

  try {
    const response = await auth.authorizedFetch("/api/interaction-proxy", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        actionType: "like",
        targetType: "comment",
        targetDocumentId: commentDocumentId,
      }),
    });
    if (!response.ok) {
      commentLikes.value = { ...commentLikes.value, [commentDocumentId]: previous };
      return;
    }
    const payload = await response.json().catch(() => ({}));
    commentLikes.value = { ...commentLikes.value, [commentDocumentId]: !!payload?.toggled };
  } catch {
    commentLikes.value = { ...commentLikes.value, [commentDocumentId]: previous };
  } finally {
    const next = new Set(likingIds.value);
    next.delete(commentDocumentId);
    likingIds.value = next;
  }
}

function handleReplyToggle(parentDocumentId: string) {
  isJoined.value = false;
  replyingTo.value = replyingTo.value === parentDocumentId ? null : parentDocumentId;
}

async function handleReplySubmit(payload: { parentDocumentId: string; html: string; done: (error?: string) => void }) {
  if (!auth.user.value) {
    auth.openLoginModal();
    payload.done("Vui lòng đăng nhập.");
    return;
  }
  const result = await postComment({
    authorName: auth.user.value.username,
    authorEmail: auth.user.value.email,
    content: payload.html,
    targetType: props.targetType,
    targetDocumentId: props.targetDocumentId,
    parent: payload.parentDocumentId,
  });
  if (!result.ok || !result.data) {
    payload.done(result.error ?? "Không thể gửi phản hồi.");
    return;
  }
  comments.value = [...comments.value, { ...result.data, parent: { documentId: payload.parentDocumentId } }];
  replyingTo.value = null;
  payload.done();
}
</script>
