"""Isi contoh dataset komunitas anonim untuk demo lokal secara idempoten."""

from datetime import datetime, timedelta, timezone
from uuid import NAMESPACE_URL, uuid5

from sqlalchemy import text

from app.services.store import store


SAMPLES = [
    ("Phishing/Link Berbahaya", "paket kamu ketahan nih, cek alamatnya lewat [TAUTAN] sebelum sore ya"),
    ("Phishing/Link Berbahaya", "ini undangan nikahnya, buka aja file Undangan_Kami.apk buat lihat lokasi"),
    ("Phishing/Link Berbahaya", "m-banking kamu katanya diblokir. disuruh login ulang di [TAUTAN]"),
    ("Phishing/Link Berbahaya", "ada tagihan belum dibayar, detailnya dikirim dalam file Tagihan.apk"),
    ("Social Engineering", "Bu saya dari pihak bank, boleh sebutkan kode OTP yang baru masuk?"),
    ("Social Engineering", "ini nomor baruku. tolong transfer dulu ke rekening [NOMOR_SENSITIF], besok kuganti"),
    ("Social Engineering", "akunmu akan ditutup hari ini kalau PIN-nya belum diverifikasi"),
    ("Social Engineering", "saya petugas ekspedisi, kirim foto KTP untuk konfirmasi paketnya ya"),
    ("Penipuan Investasi", "lagi ada grup cuan, modal 300 ribu katanya malam ini balik dua kali lipat"),
    ("Penipuan Investasi", "ikut trading ini aja, profitnya dijamin dan nggak mungkin rugi"),
    ("Penipuan Investasi", "slot investasi tinggal satu, transfer sekarang biar bonusnya nggak hangus"),
    ("Penipuan Rekrutmen", "kak lolos kerja part time. sebelum mulai bayar biaya admin 150 ribu dulu"),
    ("Penipuan Rekrutmen", "interview-nya lewat chat aja, tapi seragam wajib dibayar hari ini"),
    ("Penipuan Rekrutmen", "kami dari HR, kirim foto KTP dan nomor rekening sebelum tes ya"),
    ("Penipuan Romansa", "sayang aku lagi darurat di luar kota, bisa kirim uang dulu malam ini?"),
    ("Penipuan Romansa", "hadiah buat kamu tertahan bea cukai, bantu bayar supaya cepat sampai"),
    ("Penipuan Romansa", "aku serius mau ketemu, cuma tiketnya kurang. bisa transfer ke [NOMOR_SENSITIF]?"),
    ("Phishing/Link Berbahaya", "poin belanja kamu mau hangus malam ini, tukarkan lewat [TAUTAN] ya"),
    ("Phishing/Link Berbahaya", "katanya ada foto kita di sini, coba buka [TAUTAN] deh"),
    ("Phishing/Link Berbahaya", "surat tilang elektroniknya bisa dicek di file ETLE_Pemberitahuan.apk"),
    ("Phishing/Link Berbahaya", "akun email perlu diperbarui, masuk lewat [TAUTAN] agar tetap aktif"),
    ("Phishing/Link Berbahaya", "resi pengiriman gagal dilacak, instal aplikasi Cek_Resi.apk dulu"),
    ("Phishing/Link Berbahaya", "voucher gratis khusus hari ini, klaim sekarang di [TAUTAN] sebelum habis"),
    ("Social Engineering", "Mas, saya kasirnya. pembayaran tadi gagal, boleh kirim bukti mutasi lengkap?"),
    ("Social Engineering", "Pa ini anakmu pinjam hp teman, segera kirim uang ke [NOMOR_SENSITIF] ya"),
    ("Social Engineering", "untuk membatalkan transaksi mencurigakan, sebutkan tiga angka di belakang kartu"),
    ("Social Engineering", "saya dari layanan dompet digital, share layar sebentar biar akun bisa dipulihkan"),
    ("Social Engineering", "data bantuanmu belum cocok, kirim foto KK dan selfie pegang KTP sekarang"),
    ("Social Engineering", "jangan hubungi kantor dulu, proses ini rahasia. ikuti arahan saya lewat telepon"),
    ("Penipuan Investasi", "deposit 500rb dapat profit harian 15%, nanti modal bisa ditarik kapan aja"),
    ("Penipuan Investasi", "robot trading baru buka member, hasilnya otomatis dan dijamin balik modal"),
    ("Penipuan Investasi", "aku sudah cair berkali-kali dari aplikasi ini, daftar lewat [TAUTAN] biar dapat bonus"),
    ("Penipuan Investasi", "gabung arisan online yuk, setor sekali terus dapat giliran paling awal"),
    ("Penipuan Investasi", "koin ini bakal naik malam nanti, beli sekarang sebelum diumumkan ke publik"),
    ("Penipuan Investasi", "keuntungan kebun digital bisa 30% sebulan, slot mitra tinggal sedikit"),
    ("Penipuan Rekrutmen", "selamat kamu diterima kerja remote, aktivasi akun pegawai bayar 75 ribu ya"),
    ("Penipuan Rekrutmen", "lowongan admin tanpa pengalaman, hubungi [AKUN] lalu isi data rekening untuk gaji"),
    ("Penipuan Rekrutmen", "tes kerja cukup kasih rating produk, tapi saldo tugas harus diisi dulu"),
    ("Penipuan Rekrutmen", "jadwal training besok. biaya penginapan transfer dulu, nanti diganti perusahaan"),
    ("Penipuan Rekrutmen", "CV kamu kami terima, lanjut wawancara lewat [TAUTAN] dan unduh aplikasi meetingnya"),
    ("Penipuan Rekrutmen", "ada kerja freelance gampang, kirim email dan kode OTP pendaftaran ke HR"),
    ("Penipuan Romansa", "aku mau kirim hadiah dari luar negeri, kamu cuma perlu bayar ongkir dan pajaknya"),
    ("Penipuan Romansa", "sayang, rekeningku sedang dibekukan. pinjami dulu buat biaya rumah sakit ibu"),
    ("Penipuan Romansa", "kita memang belum pernah ketemu, tapi aku percaya kamu. bantu bayar tiket pulang ya"),
    ("Penipuan Romansa", "aku anggota militer yang sedang tugas, butuh bantuan biaya agar paketku bisa keluar"),
    ("Penipuan Romansa", "setelah ngobrol beberapa hari aku yakin sama kamu, boleh pinjam akun bankmu sebentar?"),
    ("Penipuan Romansa", "aku sudah belikan cincin, tapi kurir minta biaya pelepasan. bisa bantu transfer?"),
]


def main() -> None:
    now = datetime.now(timezone.utc)
    added = 0
    with store.lock, store.engine.begin() as db:
        for index, (category, message) in enumerate(SAMPLES):
            key = f"nusaguard-community-seed-{index}"
            report_id = str(uuid5(NAMESPACE_URL, f"{key}-report"))
            dataset_id = str(uuid5(NAMESPACE_URL, f"{key}-dataset"))
            created = now - timedelta(days=index % 7)

            db.execute(
                text(
                    "INSERT INTO reports(id,text,category_suggested,status,created_at) "
                    "SELECT :id,:message,:category,'approved',:created "
                    "WHERE NOT EXISTS (SELECT 1 FROM reports WHERE id=:id)"
                ),
                {
                    "id": report_id,
                    "message": message,
                    "category": category,
                    "created": created,
                },
            )
            result = db.execute(
                text(
                    "INSERT INTO public_dataset(id,report_id,text_anonymized,category,provenance,reviewed,created_at) "
                    "SELECT :id,:report_id,:message,:category,'synthetic_community_seed',TRUE,:created "
                    "WHERE NOT EXISTS (SELECT 1 FROM public_dataset WHERE id=:id OR report_id=:report_id)"
                ),
                {
                    "id": dataset_id,
                    "report_id": report_id,
                    "message": message,
                    "category": category,
                    "created": created,
                },
            )
            added += max(result.rowcount, 0)

    print(f"Seeder dataset komunitas selesai: {added} sampel baru, {len(SAMPLES)} tersedia.")


if __name__ == "__main__":
    main()
