# Trekky Django Migration

Target structure:

```text
django/
  admin/
  admin-app/
web/
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

## Web

```powershell
cd web
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

This runs Django and Next.js in one terminal. `Ctrl+C` stops both.

This scaffold includes:

- Django 6.0.3 backend
- DRF + SimpleJWT APIs
- Bootstrap-based `admin-app`
- Next.js `web` starter with public and moderator routes
- Import command skeleton for Strapi content

## Docker And CI/CD

Production deployment files live in:

- `deploy/docker/api.Dockerfile`
- `web/Dockerfile`
- `deploy/vps/docker-compose.yml`
- `deploy/vps/deploy.sh`
- `.github/workflows/deploy.yml`

GitHub Actions is set up to:

1. Build and push the Django API image to Docker Hub
2. Build and push the Next.js web image to Docker Hub
3. Copy deploy files to `~/projects/trekky-net` on the VPS
4. Run `deploy.sh` on the VPS to pull images, migrate, collect static files, and restart containers

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

- `NEXT_PUBLIC_API_URL`
- `NEXT_PUBLIC_SITE_URL`
- `NEXT_PUBLIC_BASE_URL`

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
