# Trekky Mobile

Flutter app cho Android và iOS, đặt trong `app-flutter` và tổ chức theo kiến trúc:

```text
lib/
  app/
  core/
  shared/
  features/
```

## Chay local

```powershell
cd app-flutter
flutter pub get
flutter run --dart-define=API_BASE_URL=http://10.0.2.2:8000
```

Neu chay iOS simulator, thay `API_BASE_URL` bang dia chi backend ma simulator truy cap duoc, vi du:

```powershell
flutter run --dart-define=API_BASE_URL=http://127.0.0.1:8000
```

## Dart Define

- `APP_ENV`
- `API_BASE_URL`
- `WEB_BASE_URL`
- `OAUTH_CALLBACK_SCHEME`
- `OAUTH_CALLBACK_HOST`

Mac dinh hien tai:

- API base URL: `http://10.0.2.2:8000`
- OAuth callback: `trekky://auth`

## Scope hien tai

- Home feed
- Post detail
- Comments, like, report
- Search
- Categories, tags, public user posts
- Static pages
- Email auth
- Google OAuth callback cho mobile deep link
- Profile view/edit

## Ghi chu backend

Django da duoc mo rong de cho phep `frontend_url` voi custom mobile scheme trong Google OAuth callback. Bien moi:

```env
MOBILE_FRONTEND_SCHEMES=trekky
```
