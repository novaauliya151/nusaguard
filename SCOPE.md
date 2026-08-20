PROJECT:
NusaGuard

CORE:
IndoBERT + N-SEAE

CLIENT:
1. Web
2. Android

KILLER FEATURE:
WhatsApp notification → NusaGuard → AI analysis → warning

BACKEND:
FastAPI

WEB:
Next.js + React + Tailwind

ANDROID:
Flutter + Kotlin NotificationListenerService

AI:
IndoBERT + N-SEAE

DATABASE:
PostgreSQL

API UTAMA:
POST /analyze

PRINSIP PRIVASI:
- Data pesan dapat dikumpulkan untuk pengembangan dataset NusaGuard.
- Identitas personal seperti nama, nomor telepon, alamat, email, rekening, OTP,
  dan informasi identitas lainnya wajib dianonimkan sebelum masuk dataset publik.
- Dataset publik hanya berisi data yang telah melalui proses anonymization/de-identification.
- Data mentah yang mengandung informasi pribadi tidak dipublikasikan.
- Pengumpulan dan penggunaan data harus memiliki dasar persetujuan/izin yang sesuai.

OUT OF SCOPE:
- WhatsApp internal database
- WhatsApp Business API
- iOS
- Voice detection
- Image detection
- On-device AI
- Continual learning
- User authentication