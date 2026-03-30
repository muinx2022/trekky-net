"use client";

import { useRouter } from "next/navigation";
import { useCallback, useEffect, useState, useSyncExternalStore } from "react";
import Image from "next/image";
import { Comment } from "@/lib/strapi";
import { toAbsoluteMediaUrl } from "@/lib/seo";
import { RichTextContent } from "./rich-text-content";
import { TiptapEditor } from "./tiptap-editor";
import { useAuth } from "./auth-context";

// ─── helpers ────────────────────────────────────────────────────────────────

type GenericCommentsProps = {
  targetType: string;
  targetDocumentId: string;
  initialComments: Comment[];
};

function formatRelativeCommentTime(dateStr: string) {
  const diff = Date.now() - new Date(dateStr).getTime();
  const mins = Math.floor(diff / 60000);
  const hours = Math.floor(mins / 60);
  const days = Math.floor(hours / 24);

  if (mins < 1) return "vừa xong";
  if (mins < 60) return `${mins} phút trước`;
  if (hours < 24) return `${hours} giờ trước`;
  return `${days} ngày trước`;
}

async function postComment(
  authorizedFetch: (input: RequestInfo | URL, init?: RequestInit) => Promise<Response>,
  body: object,
): Promise<{ ok: boolean; data?: Comment; errorMsg?: string; tokenExpired?: boolean }> {
  try {
    const res = await authorizedFetch("/api/comment-proxy", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      const msg = err?.error ?? "Gửi bình luận thất bại.";
      return { ok: false, errorMsg: typeof msg === "string" ? msg : "Gửi bình luận thất bại.", tokenExpired: !!err?.tokenExpired };
    }
    const result = await res.json();
    return { ok: true, data: result?.data };
  } catch {
    return { ok: false, errorMsg: "Không thể kết nối. Vui lòng thử lại." };
  }
}

// ─── ReplyForm — self-contained; mounts fresh every time the form opens ──────

function ReplyForm({
  parentDocumentId,
  authorName,
  onSubmit,
  onCancel,
}: {
  parentDocumentId: string;
  authorName: string;
  onSubmit: (parentDocId: string, html: string) => Promise<{ ok: boolean; errorMsg?: string }>;
  onCancel: () => void;
}) {
  const [html, setHtml] = useState("");
  const [showToolbar, setShowToolbar] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState("");

  const handleSubmit = async () => {
    const content = html.trim();
    if (!content || content === "<p></p>") return;
    setSubmitting(true);
    setError("");
    const { ok, errorMsg } = await onSubmit(parentDocumentId, content);
    setSubmitting(false);
    if (!ok) setError(errorMsg ?? "Lỗi không xác định.");
    // on success the parent closes us (replyingTo → null)
  };

  return (
    <div className="rounded-2xl border border-gray-700 bg-gray-800/70 p-3 text-gray-100 shadow-[0_12px_28px_rgba(0,0,0,0.12)]">
      <p className="text-xs text-zinc-400 mb-2">Trả lời {authorName}</p>
      <div className="mb-3 rounded-xl border border-gray-700 bg-gray-800/55 p-2 transition-all focus-within:border-blue-500/60 focus-within:ring-2 focus-within:ring-blue-500/20">
        <TiptapEditor value={html} onChange={setHtml} showToolbar={showToolbar} theme="comment-dark" />
      </div>
      {error && <p className="text-xs text-red-500 mb-2">{error}</p>}
      <div className="flex justify-between items-center">
        <button onClick={() => setShowToolbar((v) => !v)} className="text-xs font-medium text-blue-300 transition-colors hover:text-blue-200">
          {showToolbar ? "Ẩn định dạng" : "Hiển thị định dạng"}
        </button>
        <div className="flex gap-2">
          <button onClick={onCancel} className="rounded-lg px-3 py-1.5 text-xs font-medium text-gray-300 transition-colors hover:bg-gray-700/70">
            Hủy
          </button>
          <button
            onClick={handleSubmit}
            disabled={submitting || !html.trim() || html === "<p></p>"}
            className="flex items-center gap-1 rounded-lg bg-blue-500 px-3 py-1.5 text-xs font-medium text-white hover:bg-blue-400 disabled:cursor-not-allowed disabled:opacity-50"
          >
            {submitting && (
              <svg className="animate-spin" xmlns="http://www.w3.org/2000/svg" width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M21 12a9 9 0 1 1-6.219-8.56"/></svg>
            )}
            Gửi
          </button>
        </div>
      </div>
    </div>
  );
}

// ─── CommentCard (module-level to avoid remount on every parent render) ──────


type CommentCardProps = {
  comment: Comment;
  depth: number;
  repliesByParent: Record<string, Comment[]>;
  replyingTo: string | null;
  isLoggedIn: boolean;
  commentLikes: Record<string, boolean>;
  likingIds: Set<string>;
  onLike: (docId: string) => void;
  onReplyToggle: (docId: string) => void;
  onReplySubmit: (parentDocId: string, html: string) => Promise<{ ok: boolean; errorMsg?: string }>;
  onReplyCancel: () => void;
  openLoginModal: () => void;
};

function CommentCard({
  comment, depth, repliesByParent, replyingTo, isLoggedIn,
  commentLikes, likingIds, onLike, onReplyToggle, onReplySubmit, onReplyCancel, openLoginModal,
}: CommentCardProps) {
  const replies = repliesByParent[comment.documentId] ?? [];
  const liked = commentLikes[comment.documentId] ?? false;
  const liking = likingIds.has(comment.documentId);
  const authorAvatarUrl = toAbsoluteMediaUrl(comment.authorAvatarUrl);

  const replyParentId = comment.documentId;

  return (
    <div>
      <div className="py-1 text-gray-100">
        <div className="mb-1 flex items-start justify-between gap-3">
          <div className="flex items-center gap-2">
            {authorAvatarUrl ? (
              <Image
                src={authorAvatarUrl}
                alt={comment.authorName ? `${comment.authorName} avatar` : "User avatar"}
                width={28}
                height={28}
                className="h-7 w-7 rounded-full bg-gray-700 object-cover ring-1 ring-gray-600"
                unoptimized
              />
            ) : (
              <div className="flex h-7 w-7 items-center justify-center rounded-full bg-gray-700 text-xs font-bold uppercase text-blue-200 ring-1 ring-gray-600">
                {comment.authorName?.[0] ?? "?"}
              </div>
            )}
            <p className="text-sm font-semibold text-gray-100">{comment.authorName}</p>
          </div>
          <span className="text-xs text-gray-400">{formatRelativeCommentTime(comment.createdAt)}</span>
        </div>
        <RichTextContent html={comment.content} className="richtext-content pl-9 text-gray-300" />

        <div className="mt-2 flex gap-3 pl-9">
          <button
            onClick={() => onLike(comment.documentId)}
            disabled={liking}
            className={`flex items-center gap-1 text-xs font-medium transition-colors ${
              liked ? "text-red-400" : "text-gray-400 hover:text-red-400"
            }`}
          >
            <svg xmlns="http://www.w3.org/2000/svg" width="13" height="13" viewBox="0 0 24 24" fill={liked ? "currentColor" : "none"} stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M19 14c1.49-1.46 3-3.21 3-5.5A5.5 5.5 0 0 0 16.5 3c-1.76 0-3 .5-4.5 2-1.5-1.5-2.74-2-4.5-2A5.5 5.5 0 0 0 2 8.5c0 2.3 1.5 4.05 3 5.5l7 7Z"/></svg>
            Thích
          </button>
          <button
            onClick={() => {
              if (!isLoggedIn) { openLoginModal(); return; }
              onReplyToggle(comment.documentId);
            }}
            className="text-xs font-medium text-gray-400 transition-colors hover:text-blue-300"
          >
            {replies.length > 0 ? `Trả lời (${replies.length})` : "Trả lời"}
          </button>
        </div>
      </div>

      {replies.length > 0 && (
        <div className="ml-3 mt-2 space-y-2 border-l border-gray-700/70 pl-5">
          {replies.map((reply) => (
            <CommentCard
              key={reply.documentId}
              comment={reply}
              depth={depth + 1}
              repliesByParent={repliesByParent}
              replyingTo={replyingTo}
              isLoggedIn={isLoggedIn}
              commentLikes={commentLikes}
              likingIds={likingIds}
              onLike={onLike}
              onReplyToggle={onReplyToggle}
              onReplySubmit={onReplySubmit}
              onReplyCancel={onReplyCancel}
              openLoginModal={openLoginModal}
            />
          ))}
        </div>
      )}

      {replyingTo === comment.documentId && (
        <div className="ml-3 mt-2 border-l border-gray-700/70 pl-5">
          <ReplyForm
            parentDocumentId={replyParentId}
            authorName={comment.authorName}
            onSubmit={onReplySubmit}
            onCancel={onReplyCancel}
          />
        </div>
      )}
    </div>
  );
}

// ─── Main component ──────────────────────────────────────────────────────────

export function GenericComments({ targetType, targetDocumentId, initialComments }: GenericCommentsProps) {
  const router = useRouter();
  const { isLoggedIn, user, jwt, openLoginModal, logout, authorizedFetch } = useAuth();
  const isHydrated = useSyncExternalStore(
    () => () => {},
    () => true,
    () => false,
  );
  const isAuthed = isHydrated && isLoggedIn;
  const authUser = isHydrated ? user : null;
  const authJwt = isHydrated ? jwt : null;

  // Main comment box
  const [isJoined, setIsJoined] = useState(false);
  const [commentHtml, setCommentHtml] = useState("");
  const [showToolbar, setShowToolbar] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [successMsg, setSuccessMsg] = useState("");
  const [errorMsg, setErrorMsg] = useState("");

  // Flat list — top-level + replies

  // Per-comment like: documentId → liked (optimistic)
  const [commentLikes, setCommentLikes] = useState<Record<string, boolean>>({});
  const [likingIds, setLikingIds] = useState<Set<string>>(new Set());

  // Reply state
  const [replyingTo, setReplyingTo] = useState<string | null>(null);

  const loadCommentLikeState = useCallback(async () => {
    if (!isAuthed || !authJwt) {
      setCommentLikes({});
      return;
    }

    try {
      const res = await authorizedFetch(`/api/interaction-proxy?targetType=${encodeURIComponent("comment")}`, {
        cache: "no-store",
      });
      const payload = await res.json();
      const interactions: Array<{ actionType?: string; targetDocumentId?: string }> = payload?.data ?? [];
      const likedMap: Record<string, boolean> = {};
      for (const item of interactions) {
        if (item?.actionType === "like" && item.targetDocumentId) {
          likedMap[item.targetDocumentId] = true;
        }
      }
      setCommentLikes(likedMap);
    } catch {
      setCommentLikes({});
    }
  }, [isAuthed, authJwt, authorizedFetch]);

  useEffect(() => {
    void loadCommentLikeState();
  }, [loadCommentLikeState]);

  // Derived: top-level newest first; replies within each thread oldest first
  const topLevel = initialComments
    .filter((c) => !c.parent?.documentId)
    .sort((a, b) => new Date(b.createdAt).getTime() - new Date(a.createdAt).getTime());

  const repliesByParent: Record<string, Comment[]> = {};
  for (const c of initialComments) {
    const pid = c.parent?.documentId;
    if (pid) {
      if (!repliesByParent[pid]) repliesByParent[pid] = [];
      repliesByParent[pid].push(c);
    }
  }
  for (const pid of Object.keys(repliesByParent)) {
    repliesByParent[pid].sort((a, b) => new Date(a.createdAt).getTime() - new Date(b.createdAt).getTime());
  }

  const handleJoinClick = () => {
    if (!isAuthed) { openLoginModal(); return; }
    setIsJoined(true);
  };

  const handlePostComment = async () => {
    if (!authUser || !authJwt) { openLoginModal(); return; }
    const content = commentHtml.trim();
    if (!content || content === "<p></p>") return;

    setSubmitting(true);
    setErrorMsg("");
    const { ok, errorMsg: err, tokenExpired } = await postComment(authorizedFetch, {
      authorName: authUser.username, authorEmail: authUser.email,
      content, targetType, targetDocumentId,
    });
    setSubmitting(false);
    if (!ok) {
      if (tokenExpired) { logout(); openLoginModal(); return; }
      setErrorMsg(err ?? "Lỗi không xác định."); return;
    }

    setIsJoined(false);
    setCommentHtml("");
    setSuccessMsg("Cảm ơn bạn đã tham gia bình luận!");
    router.refresh();
    setTimeout(() => setSuccessMsg(""), 5000);
  };

  const handleLikeComment = async (commentDocumentId: string) => {
    if (!isAuthed || !authJwt) { openLoginModal(); return; }
    // Optimistic toggle
    const prev = commentLikes[commentDocumentId] ?? false;
    setCommentLikes((s) => ({ ...s, [commentDocumentId]: !prev }));
    setLikingIds((s) => new Set(s).add(commentDocumentId));
    try {
      const res = await authorizedFetch("/api/interaction-proxy", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ actionType: "like", targetType: "comment", targetDocumentId: commentDocumentId }),
      });
      if (res.ok) {
        const data = await res.json();
        setCommentLikes((s) => ({ ...s, [commentDocumentId]: !!data?.toggled }));
        void loadCommentLikeState();
      } else {
        // Revert on failure
        setCommentLikes((s) => ({ ...s, [commentDocumentId]: prev }));
      }
    } catch {
      setCommentLikes((s) => ({ ...s, [commentDocumentId]: prev }));
    } finally {
      setLikingIds((s) => { const n = new Set(s); n.delete(commentDocumentId); return n; });
    }
  };

  const handleReplyToggle = (parentDocumentId: string) => {
    setReplyingTo((prev) => prev === parentDocumentId ? null : parentDocumentId);
  };

  const handleReplyCancel = () => {
    setReplyingTo(null);
  };

  const handleReplySubmit = async (parentDocumentId: string, html: string): Promise<{ ok: boolean; errorMsg?: string }> => {
    if (!authUser || !authJwt) { openLoginModal(); return { ok: false, errorMsg: "Vui lòng đăng nhập." }; }

    const { ok, data, errorMsg: err, tokenExpired } = await postComment(authorizedFetch, {
      authorName: authUser.username, authorEmail: authUser.email,
      content: html, targetType, targetDocumentId,
      parent: parentDocumentId,
    });
    if (!ok) {
      if (tokenExpired) { logout(); openLoginModal(); }
      return { ok: false, errorMsg: err ?? "Lỗi không xác định." };
    }

    // Always build the optimistic object manually — Strapi's create response
    // does not populate the parent relation, so we must not use data.parent
    const newReply: Comment = data
      ? {
          ...data,
          parent: { documentId: parentDocumentId },
          authorAvatarUrl: data.authorAvatarUrl ?? authUser.avatarUrl ?? null,
        }
      : {
          id: Date.now(),
          documentId: String(Date.now()),
          authorName: authUser.username,
          authorAvatarUrl: authUser.avatarUrl ?? null,
          content: html,
          targetType: targetType as Comment["targetType"],
          targetDocumentId,
          createdAt: new Date().toISOString(),
          parent: { documentId: parentDocumentId },
        };
    void newReply;
    setReplyingTo(null);
    router.refresh();
    return { ok: true };
  };

  return (
    <div className="space-y-6">
      {successMsg && (
        <div className="flex items-center gap-2 text-sm text-green-700 dark:text-green-400 bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 rounded-lg px-4 py-3">
          <svg xmlns="http://www.w3.org/2000/svg" width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><path d="m9 11 3 3L22 4"/></svg>
          {successMsg}
        </div>
      )}
      {errorMsg && (
        <div className="flex items-center gap-2 text-sm text-red-600 dark:text-red-400 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg px-4 py-3">
          <svg xmlns="http://www.w3.org/2000/svg" width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><circle cx="12" cy="12" r="10"/><line x1="12" x2="12" y1="8" y2="12"/><line x1="12" x2="12.01" y1="16" y2="16"/></svg>
          {errorMsg}
        </div>
      )}

      {/* Main comment box */}
      {!isJoined ? (
        <div
          onClick={handleJoinClick}
          className="flex w-full cursor-pointer items-center gap-3 rounded-2xl border border-dashed border-gray-700 bg-gray-800/35 px-4 py-3 text-gray-200 transition-colors hover:border-blue-500/50 hover:bg-gray-800/55"
        >
          <svg xmlns="http://www.w3.org/2000/svg" width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="shrink-0 text-gray-400"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/></svg>
          <p className="text-sm text-gray-400">
            {isAuthed ? "Nhấn để tham gia thảo luận..." : "Đăng nhập để bình luận..."}
          </p>
        </div>
      ) : (
        <div className="rounded-2xl border border-gray-700 bg-gray-800/62 p-4 text-gray-100 shadow-[0_12px_28px_rgba(0,0,0,0.12)]">
          <div className="mb-4 rounded-xl border border-gray-700 bg-gray-700/45 p-3 transition-all focus-within:border-blue-500/60 focus-within:ring-2 focus-within:ring-blue-500/20">
            <TiptapEditor value={commentHtml} onChange={setCommentHtml} showToolbar={showToolbar} theme="comment-dark" />
          </div>
          <div className="flex justify-between items-center">
            <button onClick={() => setShowToolbar(!showToolbar)} className="text-xs font-medium text-blue-300 transition-colors hover:text-blue-200">
              {showToolbar ? "Ẩn định dạng" : "Hiển thị định dạng"}
            </button>
            <div className="flex gap-2">
              <button
                onClick={() => { setIsJoined(false); setErrorMsg(""); }}
                className="rounded-lg px-4 py-2 text-sm font-medium text-gray-300 transition-colors hover:bg-gray-700/70"
              >
                Hủy
              </button>
              <button
                onClick={handlePostComment}
                disabled={submitting || !commentHtml.trim() || commentHtml === "<p></p>"}
                className="flex items-center gap-2 rounded-lg bg-blue-500 px-4 py-2 text-sm font-medium text-white hover:bg-blue-400 disabled:cursor-not-allowed disabled:opacity-50"
              >
                {submitting && (
                  <svg className="animate-spin" xmlns="http://www.w3.org/2000/svg" width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M21 12a9 9 0 1 1-6.219-8.56"/></svg>
                )}
                Bình luận
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Comment list */}
      <div className="mt-8 space-y-4">
        {topLevel.map((comment) => (
          <CommentCard
            key={comment.documentId}
            comment={comment}
            depth={0}
            repliesByParent={repliesByParent}
            replyingTo={replyingTo}
            isLoggedIn={isAuthed}
            commentLikes={commentLikes}
            likingIds={likingIds}
            onLike={handleLikeComment}
            onReplyToggle={handleReplyToggle}
            onReplyCancel={handleReplyCancel}
            onReplySubmit={handleReplySubmit}
            openLoginModal={openLoginModal}
          />
        ))}
        {topLevel.length === 0 && (
          <div className="rounded-2xl border border-gray-700 bg-gray-800/30 px-4 py-8 text-center text-sm text-gray-400">
            Chưa có bình luận nào. Hãy là người đầu tiên!
          </div>
        )}
      </div>
    </div>
  );
}



