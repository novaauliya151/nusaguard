# NusaGuard

Prototype anti-penipuan berbahasa Indonesia: pesan manual dari web atau teks notifikasi WhatsApp baru dari Android dikirim ke satu FastAPI API, dianalisis oleh IndoBERT (jika model fine-tuned tersedia) dan enam indikator N-SEAE, lalu dikembalikan sebagai skor risiko, kategori, alasan, dan rekomendasi.

## Status MVP

- Web analysis UI, layered result, education, privacy disclosure, large-text and high-contrast modes
- FastAPI `/api/analyze`, `/api/categories`, `/api/report`, `/api/stats`, `/health`
- Six-indicator N-SEAE lexicon scoring and explicit rules fallback
- PostgreSQL reports/aggregate statistics (`DATABASE_URL`), SQLite local fallback
- Flutter client + native Kotlin `NotificationListenerService` source
- IndoBERT fine-tuning/evaluation pipeline
- Balanced synthetic development dataset: 500 samples for each of six categories, with provenance/review metadata
- Docker/Render blueprint and GitHub Actions

The analyzed message is never stored. Only an explicitly consented `/api/report` submission stores text. Logs contain method, path, status, and response time—not message bodies, contacts, or phone numbers.

## Run locally

```bash
cd backend
python -m venv .venv
.venv/Scripts/pip install -r requirements.txt
.venv/Scripts/python -m uvicorn app.main:app --reload
```

```bash
cd frontend
npm ci
# copy .env.example to .env.local if the API is not localhost:8000
npm run dev
```

### Dashboard admin

Migrasi admin bersifat idempoten dan mempertahankan data lama. Untuk instalasi baru, gunakan environment variable agar kredensial tidak ditulis di source code:

```powershell
cd backend
$env:INITIAL_ADMIN_NAME="Super Admin NusaGuard"
$env:INITIAL_ADMIN_EMAIL="admin@example.com"
$env:INITIAL_ADMIN_PASSWORD="password-kuat-minimal-10-karakter"
.\.venv\Scripts\python.exe -m scripts.migrate_admin
.\.venv\Scripts\python.exe -m scripts.seed_admin
```

Role internal utama adalah `super_admin`, `validator`, dan `content_editor`. Role lama tetap dikenali untuk kompatibilitas. Permission granular disimpan pada tabel `permissions` dan `role_permissions`, diperiksa ulang oleh setiap endpoint backend, dan digunakan frontend untuk menyaring menu. Login dibatasi lima kegagalan per alamat/IP selama 15 menit; logout, pemblokiran, dan reset password mencabut sesi yang relevan. Penghapusan pengguna memakai soft delete dan Super Admin terakhir dilindungi.

Buat akun admin awal dari terminal backend:

```bash
.venv/Scripts/python -m scripts.create_admin
```

User dan admin masuk melalui halaman yang sama, `http://localhost:3000/login`. Backend membaca role dari database: user diarahkan ke `/dashboard`, sedangkan admin diarahkan ke `/admin`. Tidak ada pilihan role pada formulir login dan seluruh endpoint `/api/admin/*` memverifikasi bearer token serta role admin pada setiap permintaan. Dashboard hanya menampilkan statistik agregat dan laporan yang dikirim pengguna dengan persetujuan; isi analisis biasa tetap tidak disimpan.

Seluruh fitur admin berada pada `/admin` dan kode tiap fiturnya dipisahkan sebagai file datar, misalnya `admin.dashboard.tsx` dan `admin.manajemen-pengguna.tsx`. Manajemen pengguna menyediakan pencarian, filter, pembuatan melalui modal, edit profil/password/role, aktivasi atau pemblokiran, dan penghapusan akun.

### Akun pengguna dan role

Pengguna dapat mendaftar melalui `http://localhost:3000/register`, masuk melalui `/login`, lalu memakai `/dashboard`. Registrasi publik selalu menghasilkan role `user`; role tidak pernah dipercaya dari input frontend. Password disimpan sebagai hash PBKDF2 dan sesi database berlaku tujuh hari. Role yang tersedia adalah `user`, `analyst`, `moderator`, dan `admin`; pengelolaannya tersedia pada menu **Manajemen pengguna** di dashboard admin. Analisis tanpa login tetap tersedia pada halaman publik.

### Edukasi, laporan, dan dataset publik

- `/education`: edukasi modus dinamis yang dikelola admin.
- `/report`: laporan sukarela dengan consent eksplisit dan larangan menyertakan identitas pribadi.
- `/dataset`: laporan `reviewed` yang sudah dianonimkan dan dapat diunduh sebagai CSV.

Admin mengelola edukasi melalui menu **Edukasi modus**. Laporan hanya dapat diproses ke dataset setelah ditinjau; email, nomor telepon, akun, tautan, nomor sensitif, dan alamat yang terdeteksi diganti placeholder sebelum publikasi. Identitas akun pelapor tidak dikaitkan dengan laporan.

## Model and measured results

The verified base model is `indobenchmark/indobert-base-p1`. Run `backend/training/train_indobert.py` on a CUDA-capable machine to create `backend/model/indobert/evaluation.json`. Until that artifact exists, responses honestly return `model_source: rules-fallback`.

`backend/evaluation/demo_results.json` records the current curated ten-message demo smoke test. It is not a held-out model benchmark and must never be presented as IndoBERT accuracy.

### IndoBERT + N-SEAE fusion

N-SEAE now scores multiple linguistic signals per indicator, aggregates cross-indicator synergy, recognizes protective/negated contexts, and can rerank an IndoBERT result when the psychological evidence conflicts with the model. API responses expose `model_confidence`, `nseae_risk_score`, and `fusion_applied` so the intervention remains auditable.

Run the reproducible development ablation with:

```bash
cd backend
.venv-ml/Scripts/python evaluation/evaluate_nseae_ablation.py
```

`backend/evaluation/nseae_ablation_results.json` compares IndoBERT alone with IndoBERT + N-SEAE on a curated 24-message challenge set. This small challenge set is useful for regression testing, not a held-out real-world benchmark or a production accuracy claim.

## Deploy

1. Create a Render Blueprint from `render.yaml`; set `CORS_ORIGINS` to the final web origin.
2. Deploy `frontend` to Vercel and set `NEXT_PUBLIC_API_URL` to the HTTPS Render URL.
3. Train the model, copy its exported files into `backend/model/indobert`, and redeploy the API image.
4. Build Android with `--dart-define=API_URL=https://...`; production must disable cleartext traffic.

Live deployment, an Android APK, and a real WhatsApp device demonstration require the owner's provider credentials, Flutter/Android SDK, and physical device permission. These cannot be fabricated by CI.

## Demo checklist

- Open web, analyze one benign and one suspicious message.
- Show all six indicator scores and the recommended action.
- On Android, explain notification-access consent, then grant it.
- Send a controlled WhatsApp test message containing urgency + OTP; show the warning notification.
- Open education and privacy sections.
- State the actual held-out accuracy/F1 from `evaluation.json`, not the proposal target.


