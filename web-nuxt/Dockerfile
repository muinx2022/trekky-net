FROM node:22-alpine AS deps

WORKDIR /app
COPY package.json package-lock.json* ./
RUN npm install

FROM node:22-alpine AS builder

WORKDIR /app
ARG NUXT_PUBLIC_API_URL=https://api.trekky.net
ARG NUXT_PUBLIC_SITE_URL=https://trekky.net
ARG NUXT_PUBLIC_BASE_URL=https://trekky.net
ARG NUXT_PUBLIC_GA4_MEASUREMENT_ID=
ARG NUXT_API_URL=https://api.trekky.net
ENV NUXT_PUBLIC_API_URL=$NUXT_PUBLIC_API_URL
ENV NUXT_PUBLIC_SITE_URL=$NUXT_PUBLIC_SITE_URL
ENV NUXT_PUBLIC_BASE_URL=$NUXT_PUBLIC_BASE_URL
ENV NUXT_PUBLIC_GA4_MEASUREMENT_ID=$NUXT_PUBLIC_GA4_MEASUREMENT_ID
ENV NUXT_API_URL=$NUXT_API_URL
COPY --from=deps /app/node_modules ./node_modules
COPY . .
RUN npm run build

FROM node:22-alpine AS runner

WORKDIR /app
ENV NODE_ENV=production
COPY --from=builder /app/.output ./.output
EXPOSE 3000
CMD ["node", ".output/server/index.mjs"]
