import pandas as pd
import re
import random

random.seed(42)

# ============================================================
# 1. PROSES SMS SPAM DATASET
# ============================================================

def classify_sms_spam_row(text: str):
    """Klasifikasi baris 'spam' ke kategori NusaGuard, atau None kalau cuma promo biasa (bukan scam)."""
    t = text.lower()

    # Modus "mama/papa minta pulsa" — impersonation + urgency
    if re.search(r"(kirim|isi|beliin|transfer).{0,15}(pulsa)", t) and \
       re.search(r"(mama|papa|bpk|ibu|abah|nenek|kakak|adik|anak|penting|jgn.*tlp|jangan.*tlp|nanti.*ganti)", t):
        return "Social Engineering"

    # Phishing: iming2 hadiah/menang + link/PIN palsu
    if re.search(r"(pin|hadiah|menang|pemenang|selamat)", t) and \
       re.search(r"(klik|www\.|blogspot|jimdo|webnode|\.tk\b|\.ml\b|\.ga\b)", t):
        return "Phishing/Link Berbahaya"

    # Instruksi transfer ke rekening pribadi (modus kontrakan/rumah/jual-beli, dsb)
    if re.search(r"(transfer|rekening|a/n|rek\.|no\.rek)", t) and \
       re.search(r"(bank|bri|bni|bca|mandiri)", t):
        return "Social Engineering"

    # Pinjaman online / dana tunai tanpa jaminan
    if re.search(r"(pinjaman|dana tunai|kta|bunga.*%|bpkb)", t):
        return "Penipuan Investasi"

    # Sisanya: promo telco/e-commerce biasa (bukan scam) -> skip, jangan dipakai
    return None


def process_sms_spam(path: str) -> pd.DataFrame:
    df = pd.read_csv(path)
    df = df.dropna(subset=["Pesan"])
    rows = []
    for _, r in df.iterrows():
        pesan = str(r["Pesan"]).strip()
        if not pesan:
            continue
        if r["Kategori"] == "ham":
            rows.append({"kategori": "ham", "pesan": pesan, "kategori_nusaguard": "Aman"})
        else:
            label = classify_sms_spam_row(pesan)
            if label:
                rows.append({"kategori": "spam", "pesan": pesan, "kategori_nusaguard": label})
            # else: dilewati karena cuma promo telco biasa, bukan penipuan
    return pd.DataFrame(rows)


# ============================================================
# 2. PROSES SURVEI (kolom teks terbuka)
# ============================================================

# Urutan prioritas: kalau satu baris punya beberapa jenis, ambil yang paling spesifik dulu
CATEGORY_PRIORITY = [
    ("Permintaan OTP/PIN/password", "Social Engineering"),
    ("Mengaku sebagai bank", "Social Engineering"),
    ("Lowongan pekerjaan palsu", "Penipuan Rekrutmen"),
    ("Investasi palsu", "Penipuan Investasi"),
    ("Pinjaman online", "Penipuan Investasi"),
    ("Mengaku sebagai teman/keluarga", "Social Engineering"),
    ("Ancaman akun akan diblokir", "Social Engineering"),
    ("Modus bantuan/donasi", "Social Engineering"),
    ("Modus paket/pengiriman", "Phishing/Link Berbahaya"),
    ("Mengaku sebagai pihak pemerintah/instansi", "Social Engineering"),
    ("Link mencurigakan", "Phishing/Link Berbahaya"),
    ("Hadiah/undian", "Phishing/Link Berbahaya"),
]

# Cocokkan nama kolom pakai substring karena header aslinya panjang berisi \n dan contoh
COL_SCAM_EXAMPLE_HINT = "Tuliskan contoh pengalaman"
COL_JENIS_HINT = "Jenis pesan mencurigakan"
COL_NORMAL_HINT = "Tuliskan contoh pesan biasa"


def find_column(df: pd.DataFrame, hint: str):
    for col in df.columns:
        if hint.lower() in col.lower():
            return col
    return None


def process_survey(path: str) -> pd.DataFrame:
    df = pd.read_csv(path)
    col_scam = find_column(df, COL_SCAM_EXAMPLE_HINT)
    col_jenis = find_column(df, COL_JENIS_HINT)
    col_normal = find_column(df, COL_NORMAL_HINT)

    rows = []

    # a. Contoh pesan penipuan asli dari responden
    for _, r in df.iterrows():
        text = str(r.get(col_scam, "")).strip()
        jenis = str(r.get(col_jenis, "")).strip()

        if not text or text.lower() in ("nan", "tidak ada", "tidak pernah", "-", ""):
            continue

        # tentukan kategori berdasarkan prioritas jenis yang dicentang
        label = "Social Engineering"  # default fallback kalau tidak match apapun
        for keyword, cat in CATEGORY_PRIORITY:
            if keyword.lower() in jenis.lower():
                label = cat
                break

        rows.append({"kategori": "spam", "pesan": text, "kategori_nusaguard": label})

    # b. Contoh pesan normal dari responden -> Aman
    for _, r in df.iterrows():
        text = str(r.get(col_normal, "")).strip()
        if not text or text.lower() in ("nan", "tidak ada", "-", ""):
            continue
        rows.append({"kategori": "ham", "pesan": text, "kategori_nusaguard": "Aman"})

    return pd.DataFrame(rows)


# ============================================================
# 3. DATA SINTETIS: PENIPUAN ROMANSA (20 contoh)
# ============================================================

ROMANCE_SCAM_TEMPLATES = [
    "Sayang, maaf baru bisa chat. Kerjaan di rig lagi padat banget. Btw aku kirim paket buat kamu ya, isinya perhiasan sama uang tunai.",
    "Aku beneran sayang kamu meski kita belum ketemu langsung. Cuma masalahnya paket yang aku kirim ketahan di bea cukai, butuh biaya pajak dulu buat ambil.",
    "Halo cantik, aku tentara yang lagi tugas di luar negeri. Boleh kenalan? Aku serius pengen serius sama kamu.",
    "Sayang, dompet aku ketinggalan pas mau pulang. Bisa pinjemin dulu buat beli tiket pesawat? Nanti aku ganti double pas udah sampai.",
    "Aku pengen banget nikahin kamu, tapi ada kendala biaya administrasi buat pensiun dini dari kerjaan. Bisa bantu dulu ga?",
    "Kangen banget sama kamu. Btw HP aku lagi rusak, ini pake HP temen. Kirimin pulsa dulu ya biar bisa telpon kamu.",
    "Aku dokter yang lagi tugas kemanusiaan di Yaman. Setelah ini aku mau pulang ke Indonesia buat nemuin kamu, tapi butuh dana darurat visa.",
    "Sayang aku transfer $50000 buat kita berdua tapi harus ada yang jemput di bandara dan bayar biaya custom dulu, bisa bantu?",
    "Aku pengusaha minyak dari luar negeri, ketemu kamu di aplikasi kencan rasanya beda. Mau kenalan lebih jauh?",
    "Maaf sayang, kartu ATM aku diblokir gara-gara transaksi luar negeri. Bisa transferin dulu buat kebutuhan sehari-hari?",
    "Aku captain kapal yang lagi berlayar, sinyal susah. Tiap chat mahal banget, bisa top up pulsa buat aku dulu?",
    "Kita udah chat 3 bulan, aku pengen ketemu kamu langsung tapi tiket pesawatnya mahal. Bisa bantu beliin dulu?",
    "Sayang, ibuku sakit keras di kampung dan butuh biaya operasi mendesak. Aku lagi di luar negeri jadi susah transfer langsung.",
    "Aku insinyur minyak lepas pantai, gajiku besar tapi belum cair karena masalah administrasi bank luar negeri. Bisa pinjemin sementara?",
    "Hai, kita cocok banget kayaknya. Aku mau kirim hadiah spesial buat kamu tapi butuh bantuan bayar ongkir internasional dulu.",
    "Sayang, laptop kerjaanku rusak dan aku butuh itu buat video call sama kamu tiap hari. Bisa bantu beliin yang baru?",
    "Aku PBB officer yang ditugaskan di Afrika, pengen banget serius sama kamu. Tapi ada dana emergency yang harus aku keluarin dulu.",
    "Kamu beda dari yang lain, aku jarang buka hati ke orang. Btw bisa minjemin uang buat bayar visa kunjungan ke Indonesia?",
    "Sayang paket hadiah dari aku ketahan di bandara, aku minta kamu transfer biaya denda supaya bisa langsung dikirim ke alamat kamu.",
    "Aku lagi proses cerai dan butuh dukungan finansial sementara sambil urus semuanya. Kamu orang yang paling ngerti aku sekarang.",
]

def build_romance_scam_df() -> pd.DataFrame:
    return pd.DataFrame([
        {"kategori": "spam", "pesan": t, "kategori_nusaguard": "Penipuan Romansa"}
        for t in ROMANCE_SCAM_TEMPLATES
    ])

# ============================================================
# 3b. DATA SINTETIS: PENIPUAN REKRUTMEN (15 contoh)
# ============================================================

RECRUITMENT_SCAM_TEMPLATES = [
    "Halo kak, ada lowongan kerja part time dari rumah. Cuma follow & like akun sosmed brand kami, dibayar 150rb per hari. Minat? Chat kami ya.",
    "Selamat! Kamu terpilih jadi karyawan online PT Maju Bersama. Gaji 5jt/bulan, kerja dari HP. Isi data diri dan bayar deposit seragam 250rb dulu ya.",
    "Dibutuhkan segera admin online, gaji harian langsung cair. Modal awal cuma beli starter kit 100rb, langsung kerja hari ini juga!",
    "Kak, mau kerja sampingan ga? Tugasnya cuma rating produk di aplikasi, komisi 50rb per tugas. Daftar dulu ya, transfer biaya aktivasi akun 75rb.",
    "Loker WFH tanpa pengalaman, gaji 3jt/minggu! Cukup share link ke 10 grup WA, langsung dapat komisi. Chat admin untuk daftar.",
    "Kami buka lowongan reseller tanpa modal besar, cukup join member Rp 300rb dan langsung dapat produk untuk dijual, untung berlipat!",
    "Selamat kamu lolos seleksi awal jadi Brand Ambassador kami! Tinggal transfer biaya training online sebesar 150rb untuk aktivasi akun kerja.",
    "Butuh 20 orang untuk kerja like & subscribe channel YouTube, dibayar per tugas. Daftar sekarang, join grup dulu ya kak.",
    "Halo, kami dari HRD PT Sukses Mandiri. Anda diterima kerja sebagai admin input data, gaji 4jt. Kirim KTP dan bayar biaya pelatihan 200rb dulu.",
    "Kerja online cuma modal HP! Screenshot & share promo produk kami, komisi langsung cair harian. Minat? Isi form pendaftaran ini.",
    "Selamat! CV Anda lolos seleksi. Untuk proses selanjutnya, silakan transfer biaya administrasi kontrak kerja sebesar Rp250.000.",
    "Kami sedang buka lowongan freelance packing produk dari rumah, gaji 3jt/bulan, tapi wajib beli paket alat kerja seharga 175rb dulu.",
    "Dicari admin toko online, gaji 3.5jt + bonus. Kirim data diri dan transfer deposit jaminan kerja 100rb ke rekening ini.",
    "Kesempatan kerja sampingan mahasiswa! Nonton video 10 menit dapat 20rb. Daftar dulu, bayar biaya member 50rb untuk mulai.",
    "Selamat bergabung jadi partner kerja kami! Sebelum mulai, lengkapi akun dengan bayar biaya administrasi Rp99.000 ya kak.",
]

def build_recruitment_scam_df() -> pd.DataFrame:
    return pd.DataFrame([
        {"kategori": "spam", "pesan": t, "kategori_nusaguard": "Penipuan Rekrutmen"}
        for t in RECRUITMENT_SCAM_TEMPLATES
    ])


# ============================================================
# 4. GABUNGKAN SEMUA
# ============================================================

def main():
    sms_df = process_sms_spam("dataset/raw/sms_spam_indo.csv")
    survey_df = process_survey("dataset/raw/Survei Identifikasi Pesan Social Engineering di Indonesia (Jawaban) - Form Responses 1.csv")
    romance_df = build_romance_scam_df()
    recruitment_df = build_recruitment_scam_df()

    combined = pd.concat([sms_df, survey_df, romance_df, recruitment_df], ignore_index=True)

    # buang duplikat teks persis sama
    combined = combined.drop_duplicates(subset=["pesan"])

    # acak urutan biar tidak mengelompok per sumber
    combined = combined.sample(frac=1, random_state=42).reset_index(drop=True)

    combined.to_csv("dataset/processed/labeled.csv", index=False)

    print("Selesai. Ringkasan jumlah data per kategori:")
    print(combined["kategori_nusaguard"].value_counts())
    print(f"\nTotal data: {len(combined)}")


if __name__ == "__main__":
    main()