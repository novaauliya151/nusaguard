# Validasi NusaGuard

Folder ini memisahkan bukti otomatis dari studi manusia. Jalankan `python load_test.py` saat backend aktif untuk smoke load test. Uji lintas browser dan WCAG dilakukan melalui browser Chromium pada route publik utama. Hasil studi pengguna dan SUS hanya boleh diisi dari responden nyata; gunakan `sus-questionnaire.csv`, minimal mahasiswa, masyarakat umum, dan lansia, lalu hitung skor setelah persetujuan responden.

Deployment produksi memerlukan URL hosting dan secret: `DATABASE_URL`, `ADMIN_API_KEY`, `NEXT_PUBLIC_API_URL`, serta `NUSAGUARD_MODEL_REPO`. Status tidak boleh ditandai aktif sebelum URL HTTPS diverifikasi.
