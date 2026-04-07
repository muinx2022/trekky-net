<template>
  <section class="space-y-5">
    <div class="overflow-hidden rounded-[2rem] border border-slate-200 bg-white shadow-sm dark:border-slate-700 dark:bg-slate-900">
      <div class="flex flex-col gap-5 px-6 py-8 sm:px-8 lg:flex-row lg:items-end lg:justify-between lg:px-10">
        <div>
          <span class="inline-flex w-fit items-center rounded-full border border-white/70 bg-white/80 px-3 py-1 text-xs font-semibold uppercase tracking-[0.24em] text-sky-700 shadow-sm backdrop-blur dark:border-slate-500/60 dark:bg-slate-900/60 dark:text-sky-200">
            Bài viết của tôi
          </span>
          <div class="mt-3 space-y-2">
            <h1 class="text-3xl font-semibold tracking-tight text-slate-900 dark:text-slate-50 sm:text-4xl">Quản lý bài viết cá nhân</h1>
            <p class="max-w-2xl text-sm leading-6 text-slate-600 dark:text-slate-300 sm:text-base">
              Theo dõi bản nháp, cập nhật bài đã đăng và tiếp tục hoàn thiện nội dung của bạn.
            </p>
          </div>
        </div>

        <NuxtLink to="/my-posts/new" class="inline-flex w-fit items-center justify-center rounded-full bg-slate-900 px-5 py-3 text-sm font-medium text-white transition hover:bg-slate-800 dark:bg-sky-500 dark:text-slate-950 dark:hover:bg-sky-400">
          Tạo bài mới
        </NuxtLink>
      </div>
    </div>

    <MyPostsPanel />
  </section>
</template>
