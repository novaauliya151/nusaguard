# Migrasi panel admin

NusaGuard mempertahankan pola migrasi idempoten yang sudah dipakai `Store`: tabel dibuat dengan `CREATE TABLE IF NOT EXISTS` dan kolom lama ditambahkan tanpa menghapus data. Implementasinya berada di `app/services/admin_domain.py` dan dapat dijalankan dengan:

```powershell
cd backend
.\.venv\Scripts\python.exe -m scripts.migrate_admin
```

Tabel baru: `roles`, `permissions`, `role_permissions`, `nseae_validations`, `nseae_lexicons`, `action_recommendations`, `model_versions`, `analysis_statistics`, dan `system_settings`. Tabel lama `users`, `reports`, `dataset_candidates`, `education_items`, serta `admin_activity_logs` mendapat kolom tambahan untuk status, audit, soft delete, metadata AI, dan workflow validasi.

Seeder aman membaca `INITIAL_ADMIN_NAME`, `INITIAL_ADMIN_EMAIL`, dan `INITIAL_ADMIN_PASSWORD`:

```powershell
.\.venv\Scripts\python.exe -m scripts.seed_admin
```

Seeder juga membuat role sistem, permission granular, enam leksikon awal N-SEAE, rekomendasi tindakan, metadata model awal, dan pengaturan dasar. Perintah dapat dijalankan berulang kali tanpa menduplikasi data referensi.
