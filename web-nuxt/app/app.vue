<template>
  <NuxtLayout>
    <NuxtPage />
  </NuxtLayout>
</template>

<script setup lang="ts">
const theme = useTheme();
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

useHead({
  script: [
    {
      key: "theme-boot",
      innerHTML: themeBootScript,
      tagPosition: "head",
    },
  ],
});

onMounted(() => {
  theme.init();
});

onBeforeUnmount(() => {
  theme.dispose();
});
</script>
