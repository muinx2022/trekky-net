// https://nuxt.com/docs/api/configuration/nuxt-config
import tailwindcss from "@tailwindcss/vite";

export default defineNuxtConfig({
  compatibilityDate: "2025-07-15",
  devtools: { enabled: true },
  css: ["~/assets/css/main.css"],
  vite: {
    plugins: [tailwindcss()],
  },
  runtimeConfig: {
    apiUrl: process.env.STRAPI_INTERNAL_URL ?? process.env.NUXT_API_URL ?? "http://127.0.0.1:8000",
    public: {
      apiUrl: process.env.NUXT_PUBLIC_API_URL ?? "http://127.0.0.1:8000",
      siteUrl: process.env.NUXT_PUBLIC_SITE_URL ?? "http://localhost:3001",
      baseUrl: process.env.NUXT_PUBLIC_BASE_URL ?? "http://localhost:3001",
      ga4MeasurementId: process.env.NUXT_PUBLIC_GA4_MEASUREMENT_ID ?? "",
      trackerScriptUrl: "https://tracking.trekky.net/static/tracker.js?v=20260327",
      trackerId: "86abe9cf-4566-4b2e-93c8-c927080e8b2e",
    },
  },
  nitro: {
    routeRules: {
      "/api/**": { cors: true },
    },
  },
});
