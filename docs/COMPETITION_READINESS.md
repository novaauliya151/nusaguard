# Kesiapan Lomba NusaGuard

Dokumen ini memisahkan bukti yang sudah ada dari bukti yang masih harus dikumpulkan. Jangan mengubah checklist menjadi klaim sebelum artefaknya tersedia.

## Bukti teknis saat ini

- Test backend otomatis dan pemeriksaan authorization.
- Lint, type-check, dan production build frontend pada CI.
- Ablation set terkurasi 24 pesan pada `backend/evaluation/nseae_ablation_results.json`.
- Label hasil ablation secara eksplisit menyatakan bahwa data tersebut bukan benchmark dunia nyata.
- Endpoint `/health/ready` membedakan backend hidup, database siap, dan konfigurasi IndoBERT.
- Docker Compose untuk latihan deployment yang konsisten.

## Bukti yang wajib dikumpulkan sebelum klaim juara

### Benchmark dunia nyata

1. Rekrut sumber data yang sah dan sudah dianonimkan.
2. Pisahkan data sebelum pelatihan; jangan memilih contoh berdasarkan kesalahan model.
3. Gunakan minimal 60 contoh, idealnya 100–300, dengan enam kelas terwakili.
4. Dua penilai memberi label secara independen; catat penyelesaian perbedaan label.
5. Buat hash data latih agar evaluator dapat menolak kebocoran.
6. Jalankan:

```powershell
cd backend
.\.venv\Scripts\python.exe evaluation\evaluate_external_benchmark.py evaluation\external_benchmark.csv --training-hashes evaluation\training_hashes.json
```

Laporkan accuracy, macro-F1, confusion matrix, jumlah sampel per kelas, dan `fusion_delta_f1_macro`. Jangan menggunakan hasil challenge set sebagai klaim akurasi lapangan.

### Uji pengguna dan SUS

Kelompok minimum yang disarankan: mahasiswa, masyarakat umum, dan pengguna lanjut usia; idealnya sedikitnya lima peserta per kelompok untuk evaluasi formatif. Peserta menyelesaikan tugas berikut tanpa dibantu:

1. Analisis pesan tanpa login.
2. Jelaskan kategori, tingkat risiko, dan satu indikator N-SEAE.
3. Temukan panduan yang sesuai.
4. Kirim laporan anonim tanpa memasukkan data pribadi.
5. Buat akun opsional dan simpan satu hasil dengan persetujuan.
6. Hapus kembali riwayat tersebut.

Catat keberhasilan tugas, waktu, kesalahan, komentar, perangkat, dan kebutuhan aksesibilitas. Setelah tugas, isi sepuluh pertanyaan SUS skala 1–5 ke salinan `sus_responses_template.csv`, lalu jalankan:

```powershell
.\.venv\Scripts\python.exe evaluation\calculate_sus.py evaluation\sus_responses.csv
```

Jangan mengisi respons contoh atau mengarang peserta.

### Performa

Jalankan backend khusus uji, lakukan satu request pemanasan IndoBERT, lalu:

```powershell
.\.venv\Scripts\python.exe evaluation\load_test.py --requests 50 --concurrency 5 --max-p95-ms 3000
```

Catat CPU/GPU, RAM, status warm/cold model, commit model, jumlah request, error rate, throughput, p50 dan p95. Angka dari laptop lokal tidak boleh digeneralisasi menjadi performa produksi.

### Aksesibilitas dan lintas perangkat

Uji keyboard-only, zoom 200%, kontras, reduced motion, label form, pesan error, pembaca layar, serta viewport 360×800, 390×844, tablet, dan desktop. Uji Chrome, Edge, dan Firefox. Simpan tanggal, versi browser, tangkapan layar, masalah, severity, serta commit perbaikan. Targetkan WCAG 2.2 AA, tetapi jangan mengklaim patuh sebelum audit selesai.

## Alur demo 3 menit

1. Buka `/health/ready` dan tunjukkan `indobert_configured: true` sebelum presentasi.
2. Analisis contoh undangan APK tanpa login.
3. Jelaskan kategori, skor, enam indikator, dan rekomendasi—bukan hanya label.
4. Tampilkan pesan edukasi yang aman agar juri melihat pencegahan false positive.
5. Masuk sebagai user, simpan hasil anonim setelah persetujuan, lalu buka riwayat.
6. Kirim laporan dan tunjukkan moderasi admin serta dataset anonim.
7. Tutup dengan tabel benchmark eksternal dan hasil SUS asli.

Siapkan video demo lokal, ekspor database tanpa data pribadi, installer dependency, dan hotspot cadangan. Jangan mengganti hasil API dengan data palsu ketika layanan gagal; tampilkan error state dan gunakan video cadangan.

## Gate sebelum presentasi

- [ ] `/health/ready` berstatus 200 dan IndoBERT terkonfigurasi.
- [ ] Test, lint, type-check, dan build hijau pada commit yang dipresentasikan.
- [ ] Benchmark eksternal bebas kebocoran data.
- [ ] Hasil IndoBERT vs fusion tersedia beserta confusion matrix.
- [ ] Uji pengguna dan SUS asli selesai.
- [ ] Load test dan spesifikasi mesin terdokumentasi.
- [ ] Audit keyboard, zoom, kontras, mobile, dan browser selesai.
- [ ] Deployment HTTPS dan database backup diuji.
- [ ] Video demo cadangan dapat diputar tanpa internet.
