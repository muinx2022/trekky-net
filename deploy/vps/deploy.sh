#!/usr/bin/env bash
set -Eeuo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT_DIR"

if [[ ! -f .env ]]; then
  echo ".env is missing in $ROOT_DIR" >&2
  exit 1
fi

set -a
source .env
set +a

if [[ -n "${DOCKERHUB_USERNAME:-}" && -n "${DOCKERHUB_TOKEN:-}" ]]; then
  echo "$DOCKERHUB_TOKEN" | docker login -u "$DOCKERHUB_USERNAME" --password-stdin
fi

docker compose pull
docker compose up -d postgres redis meilisearch
docker compose run --rm api python manage.py migrate --noinput
docker compose run --rm api python manage.py collectstatic --noinput
docker compose up -d api worker beat web
docker compose exec -T api python manage.py meili_reindex || true

if [[ "${SYNC_STRAPI_ON_DEPLOY:-false}" == "true" ]]; then
  docker compose run --rm api python manage.py sync_strapi_postgres \
    --host "${STRAPI_SYNC_HOST}" \
    --port "${STRAPI_SYNC_PORT}" \
    --dbname "${STRAPI_SYNC_DB}" \
    --user "${STRAPI_SYNC_USER}" \
    --password "${STRAPI_SYNC_PASSWORD}" \
    --sslmode "${STRAPI_SYNC_SSLMODE:-prefer}" \
    $( [[ "${STRAPI_SYNC_DOWNLOAD_MEDIA:-true}" == "true" ]] && echo "--download-media" ) \
    --media-timeout "${STRAPI_SYNC_MEDIA_TIMEOUT:-30}"
  docker compose exec -T api python manage.py meili_reindex || true
fi
