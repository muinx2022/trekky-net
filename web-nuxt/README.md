# web-nuxt

Nuxt 4 frontend for Trekky. This app is the active replacement for the SvelteKit app in `../web`, which is kept as the parity reference during migration.

## Environment

Use these variables when running locally or in Docker:

```bash
NUXT_PUBLIC_API_URL=http://127.0.0.1:8000
NUXT_PUBLIC_SITE_URL=http://localhost:3001
NUXT_PUBLIC_BASE_URL=http://localhost:3001
NUXT_PUBLIC_GA4_MEASUREMENT_ID=
NUXT_API_URL=http://127.0.0.1:8000
```

## Development

```bash
npm install
npm run dev
```

## Build

```bash
npm run build
npm run preview
```

## Notes

- `../web` remains available for UI and behavior comparison during migration.
- The Nuxt app proxies browser-facing requests through `/api/*` and talks to Django from Nitro.
