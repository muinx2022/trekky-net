# Trekky Django Migration

Target structure:

```text
django/
  admin/
  admin-app/
web-nuxt/
```

## Backend

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
cd django/admin
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

Admin surfaces:

- `http://localhost:8000/admin/` for Django admin
- `http://localhost:8000/admin-app/` for Trekky admin app
- `http://localhost:8000/api/docs/` for OpenAPI docs

## Frontend (Nuxt 4)

```powershell
cd web-nuxt
npm install
npm run dev
```
## Run Both Apps

From the repo root:

```powershell
npm install
npm run dev
```

Or on Windows:

```powershell
.\run-dev.cmd
```

This runs Django and Nuxt 4 in one terminal. `Ctrl+C` stops both.

This scaffold includes:

- Django 6.0.3 backend
- DRF + SimpleJWT APIs
- Bootstrap-based `admin-app`
- Nuxt 4 frontend for the public Trekky site
- Import command skeleton for Strapi content

## Docker And CI/CD

Production deployment files live in:

- `deploy/docker/api.Dockerfile`
- `web-nuxt/Dockerfile`
- `deploy/vps/docker-compose.yml`
- `deploy/vps/deploy.sh`
- `deploy/vps/CUTOVER.md`
- `.github/workflows/deploy.yml`

GitHub Actions is set up to:

1. Build and push the Django API image to Docker Hub
2. Build and push the Nuxt web image to Docker Hub
3. Copy deploy files to `~/projects/trekky-net` on the VPS
4. Run `deploy.sh` on the VPS to pull images, migrate, collect static files, and restart containers

Frontend runtime variables for Nuxt:

```env
NUXT_PUBLIC_API_URL=http://127.0.0.1:8000
NUXT_API_URL=http://127.0.0.1:8000
NUXT_PUBLIC_SITE_URL=http://localhost:3001
NUXT_PUBLIC_BASE_URL=http://localhost:3001
NUXT_PUBLIC_GA4_MEASUREMENT_ID=
```

Create the VPS env file from the example:

```powershell
Copy-Item deploy\vps\.env.example deploy\vps\.env
```

Required GitHub secrets:

- `DOCKERHUB_USERNAME`
- `DOCKERHUB_TOKEN`
- `VPS_HOST`
- `VPS_USERNAME`
- `VPS_PASSWORD`
- `VPS_PORT`

Optional GitHub variables:

- `NUXT_API_URL`
- `NUXT_PUBLIC_API_URL`
- `NUXT_PUBLIC_SITE_URL`
- `NUXT_PUBLIC_BASE_URL`
- `NUXT_PUBLIC_GA4_MEASUREMENT_ID`

When you are ready to switch `trekky.net` traffic from the old Strapi stack to the new Django stack, follow `deploy/vps/CUTOVER.md`.

## Strapi Sync

There is now a direct sync command for the old Strapi Postgres database:

```powershell
cd django\admin
..\..\.venv\Scripts\python.exe manage.py sync_strapi_postgres `
  --host trekky-postgres `
  --port 5432 `
  --dbname trekky `
  --user trekky `
  --password your-password `
  --download-media
```

On the VPS, `deploy.sh` can run that import automatically when `SYNC_STRAPI_ON_DEPLOY=true` and the `STRAPI_SYNC_*` variables are filled in inside `~/projects/trekky-net/.env`.

## Media Storage

The project supports the same upload-provider pattern used by the old Strapi app.
Settings are loaded automatically from the repo-root `.env`.

Local storage:

```env
UPLOAD_PROVIDER=local
```

Cloudinary:

```env
UPLOAD_PROVIDER=cloudinary
CLOUDINARY_NAME=your-cloud-name
CLOUDINARY_KEY=your-api-key
CLOUDINARY_SECRET=your-api-secret
CLOUDINARY_SECURE=true
```

When `UPLOAD_PROVIDER=cloudinary`, Django stores `ImageField` and `FileField` media on Cloudinary instead of the local `media/` folder.

AI image search providers:

```env
GOOGLE_IMAGE_SEARCH_API_KEY=
GOOGLE_IMAGE_SEARCH_ENGINE_ID=
PEXELS_API_KEY=
```

Those keys are consumed by the Django AI automation jobs for remote image search, then the downloaded media is stored through Django's configured storage backend.
