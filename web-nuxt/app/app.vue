<template>
  <NuxtLayout>
    <NuxtPage />
  </NuxtLayout>
</template>

<script setup lang="ts">
import { buildOrganizationSchema, buildWebsiteSchema, SITE_DESCRIPTION, SITE_NAME, TWITTER_HANDLE, withSiteTitle } from "~~/shared/seo";

const theme = useTheme();
const route = useRoute();
const runtimeConfig = useRuntimeConfig();
const themeBootScript = `
(() => {
  try {
    const cookieMatch = document.cookie.match(/(?:^|; )trekky-theme=([^;]+)/);
    const cookieValue = cookieMatch ? decodeURIComponent(cookieMatch[1]) : '';
    const stored = window.localStorage.getItem('trekky-theme') || cookieValue || 'system';
    const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
    const dark = stored === 'dark' || (stored === 'system' && prefersDark);
    document.documentElement.dataset.theme = dark ? 'dark' : 'light';
    document.documentElement.style.colorScheme = dark ? 'dark' : 'light';
    document.cookie = 'trekky-theme=' + encodeURIComponent(stored) + '; path=/; SameSite=Lax';
  } catch {}
})();
`;
const scrollBootScript = `
(() => {
  try {
    const key = 'trekky:scroll:' + window.location.pathname + window.location.search;
    const raw = window.sessionStorage.getItem(key);
    if (!raw) return;
    const top = Number(raw);
    if (!Number.isFinite(top) || top <= 0) return;
    document.documentElement.dataset.scrollRestoring = '1';
    if ('scrollRestoration' in window.history) {
      window.history.scrollRestoration = 'manual';
    }
    window.scrollTo(0, top);
    const reveal = () => {
      delete document.documentElement.dataset.scrollRestoring;
    };
    const feedRestoreNeeded = window.sessionStorage.getItem('trekky:feed-restore-needed');
    if (feedRestoreNeeded) {
      window.setTimeout(reveal, 2000);
    } else {
      requestAnimationFrame(() => {
        window.scrollTo(0, top);
        requestAnimationFrame(reveal);
      });
      window.addEventListener('load', reveal, { once: true });
      window.setTimeout(reveal, 1500);
    }
  } catch {}
})();
`;

const globalSchemas = [
  buildOrganizationSchema(runtimeConfig.public.siteUrl),
  buildWebsiteSchema(runtimeConfig.public.siteUrl),
];

useHead({
  htmlAttrs: {
    lang: "vi",
  },
  titleTemplate: (titleChunk) => withSiteTitle(titleChunk),
  link: [
    {
      rel: "icon",
      type: "image/x-icon",
      href: "/favicon.ico",
    },
  ],
  meta: [
    {
      name: "viewport",
      content: "width=device-width, initial-scale=1",
    },
    {
      name: "description",
      content: SITE_DESCRIPTION,
    },
    {
      name: "application-name",
      content: SITE_NAME,
    },
    {
      name: "apple-mobile-web-app-title",
      content: SITE_NAME,
    },
    {
      name: "theme-color",
      content: "#0369a1",
    },
    {
      property: "og:site_name",
      content: SITE_NAME,
    },
    {
      property: "og:locale",
      content: "vi_VN",
    },
    {
      name: "twitter:site",
      content: TWITTER_HANDLE,
    },
    {
      name: "twitter:creator",
      content: TWITTER_HANDLE,
    },
  ],
  style: [
    {
      key: "scroll-restore-style",
      innerHTML: "html[data-scroll-restoring='1'] body { opacity: 0; }",
    },
  ],
  script: [
    {
      key: "theme-boot",
      innerHTML: themeBootScript,
      tagPosition: "head",
    },
    {
      key: "scroll-boot",
      innerHTML: scrollBootScript,
      tagPosition: "head",
    },
    {
      key: "site-schema",
      type: "application/ld+json",
      innerHTML: JSON.stringify(globalSchemas),
      tagPosition: "head",
    },
  ],
  templateParams: {
    routePath: route.path,
  },
});

onMounted(() => {
  theme.init();
});

onBeforeUnmount(() => {
  theme.dispose();
});
</script>
