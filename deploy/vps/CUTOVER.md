# Trekky Domain Cutover

Current production traffic still goes through the old `trekky-strapi` Cloudflare Tunnel targets:

- `trekky.net` -> old frontend
- `api.trekky.net` -> old Strapi API/admin

The new `trekky-net` stack is already running on the VPS and exposes stable shared-network aliases:

- `http://trekky-net-web:3000`
- `http://trekky-net-api:8000`

## Before Cutover

1. Confirm the new stack is healthy on the VPS:

   ```bash
   cd ~/projects/trekky-net
   docker compose ps
   docker compose exec -T api python manage.py check
   docker compose exec -T api python manage.py meili_reindex
   ```

2. Confirm migrated data counts:

   ```bash
   cd ~/projects/trekky-net
   docker compose exec -T api python manage.py shell -c "from trekky_apps.accounts.models import User; from trekky_apps.content.models import Post; print(User.objects.count(), Post.objects.count())"
   ```

3. Verify environment values in `~/projects/trekky-net/.env`:

   - `DJANGO_ALLOWED_HOSTS`
     Include internal API hostnames like `trekky-net-api` and `api`.
   - `DJANGO_CORS_ALLOWED_ORIGINS`
   - `DJANGO_CSRF_TRUSTED_ORIGINS`
   - `FRONTEND_URL`
   - `GOOGLE_REDIRECT_URI`

## Cloudflare Tunnel Switch

Update the existing Cloudflare Tunnel public hostname routes from the old services to the new ones:

- `trekky.net` -> `http://trekky-net-web:3000`
- `www.trekky.net` -> `http://trekky-net-web:3000`
- `api.trekky.net` -> `http://trekky-net-api:8000`

If there is a dedicated admin hostname in Cloudflare, either remove it or point it intentionally to the new stack.

## After Cutover

1. Re-test the public endpoints:

   ```bash
   curl -I https://trekky.net
   curl -I https://api.trekky.net/api/docs/
   ```

2. Check Django logs for host, CSRF, and CORS issues:

   ```bash
   cd ~/projects/trekky-net
   docker compose logs --tail 200 api
   docker compose logs --tail 200 web
   ```

3. Smoke-test login, post detail, search, media upload, and Google auth callback.

## Retire Old Stack

Only after the new domain routing is confirmed stable:

```bash
cd ~/projects/trekky-strapi
docker compose stop web admin api meilisearch
```

Keep the old Postgres container until you are satisfied with the migration backup window, then retire the remaining old services.
