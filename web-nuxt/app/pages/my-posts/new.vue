<template>
  <section class="space-y-5">
    <div class="overflow-hidden rounded-[2rem] border border-slate-200 bg-[linear-gradient(135deg,#f8fafc_0%,#e0f2fe_45%,#fff7ed_100%)] shadow-sm dark:border-slate-700 dark:bg-[linear-gradient(135deg,#0f172a_0%,#0b253a_45%,#172033_100%)]">
      <div class="px-6 py-8 sm:px-8 lg:px-10">
        <span class="inline-flex w-fit items-center rounded-full border border-white/70 bg-white/80 px-3 py-1 text-xs font-semibold uppercase tracking-[0.24em] text-sky-700 shadow-sm backdrop-blur dark:border-slate-500/60 dark:bg-slate-900/60 dark:text-sky-200">
          Tạo bài viết
        </span>
        <div class="mt-3 space-y-2">
          <h1 class="text-3xl font-semibold tracking-tight text-slate-900 dark:text-slate-50 sm:text-4xl">Tạo bài viết mới</h1>
          <p class="max-w-2xl text-sm leading-6 text-slate-600 dark:text-slate-300 sm:text-base">
            Điền nội dung bài viết và hoàn thiện thông tin cần thiết trước khi đăng.
          </p>
        </div>
      </div>
    </div>

    <PostEditorForm mode="create" />
  </section>
</template>
