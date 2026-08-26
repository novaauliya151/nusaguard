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

Set `ADMIN_API_KEY` pada environment backend, lalu buka `http://localhost:3000/admin` dan masukkan nilai kunci yang sama. Dashboard hanya menampilkan statistik agregat dan laporan yang dikirim pengguna dengan persetujuan; isi analisis biasa tetap tidak disimpan.

### Akun pengguna dan role

Pengguna dapat mendaftar melalui `http://localhost:3000/register`, masuk melalui `/login`, lalu memakai `/dashboard`. Password disimpan sebagai hash PBKDF2 dan sesi database berlaku tujuh hari. Role yang tersedia adalah `user`, `analyst`, `moderator`, dan `admin`; pengelolaannya tersedia pada menu **Manajemen pengguna** di dashboard admin. Analisis tanpa login tetap tersedia pada halaman publik.

## Model and measured results

The verified base model is `indobenchmark/indobert-base-p1`. Run `backend/training/train_indobert.py` on a CUDA-capable machine to create `backend/model/indobert/evaluation.json`. Until that artifact exists, responses honestly return `model_source: rules-fallback`.

`backend/evaluation/demo_results.json` records the current curated ten-message demo smoke test. It is not a held-out model benchmark and must never be presented as IndoBERT accuracy.

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

