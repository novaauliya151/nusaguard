# Deployment NusaGuard

## Arsitektur

- Frontend: Vercel (`frontend`)
- API dan IndoBERT: Hugging Face Docker Space (`backend`)
- Database: Supabase PostgreSQL

## 1. Publikasikan model secara privat

```powershell
hf auth login
cd backend
$env:HF_MODEL_REPO="USERNAME/nusaguard-indobert"
python scripts/publish_model.py
```

Catat commit SHA hasil unggahan. Jangan gunakan `main` untuk deployment.

## 2. Migrasikan SQLite ke Supabase

Ambil URI koneksi PostgreSQL dari Supabase, gunakan SSL, lalu jalankan:

```powershell
cd backend
$env:DATABASE_URL="postgresql+psycopg://USER:PASSWORD@HOST:5432/postgres?sslmode=require"
python scripts/migrate_sqlite_to_postgres.py --sqlite nusaguard.db
```

## 3. Hugging Face Docker Space

Buat Space privat dengan SDK Docker. Unggah isi folder `backend` sebagai root Space.
Atur Secrets/Variables berikut pada Settings Space:

```text
APP_ENV=production
DATABASE_URL=postgresql+psycopg://...?...sslmode=require
CORS_ORIGINS=https://YOUR-FRONTEND.vercel.app
ALLOWED_HOSTS=YOUR-SPACE.hf.space
NUSAGUARD_MODEL_REPO=USERNAME/nusaguard-indobert
NUSAGUARD_MODEL_REVISION=COMMIT_SHA_MODEL
HF_TOKEN=READ_ONLY_TOKEN_FOR_PRIVATE_MODEL
REQUIRE_INDOBERT=true
EXPOSE_RESET_TOKEN=false
```

Gunakan token Hugging Face khusus dengan izin baca model saja.

## 4. Vercel

Import repository, pilih Root Directory `frontend`, lalu atur:

```text
NEXT_PUBLIC_API_URL=https://YOUR-SPACE.hf.space
```

Setelah domain Vercel tersedia, perbarui `CORS_ORIGINS` pada Space.

## 5. Android produksi

```powershell
cd android
flutter build apk --release --dart-define=API_URL=https://YOUR-SPACE.hf.space
```

Build release menolak URL HTTP. HTTP lokal hanya diizinkan pada build debug.

## Pemeriksaan akhir

1. Pastikan `/health/ready` mengembalikan `ready` dan `indobert_configured: true`.
2. Buat Super Admin sekali melalui `INITIAL_ADMIN_*`, lalu hapus password dari Space.
3. Rotasi token jika pernah ditempel ke terminal, chat, commit, atau tangkapan layar.
4. Jalankan pemeriksaan secret sebelum push.
