import fs from "node:fs/promises";
import path from "node:path";

const seed = 151;
let state = seed;
const random = () => ((state = (state * 1664525 + 1013904223) >>> 0) / 2 ** 32);
const pick = (items) => items[Math.floor(random() * items.length)];

const openings = ["Halo kak", "Hai", "Selamat pagi", "Permisi", "Kepada Yth. Bapak/Ibu", "Mohon perhatian", "Info untuk Anda", "Assalamualaikum", "Selamat sore", "Halo pelanggan"];
const closings = ["Terima kasih.", "Mohon diperhatikan.", "Salam.", "Semoga membantu.", "Ditunggu konfirmasinya.", "Harap cek kembali.", "Demikian informasinya.", "Terima kasih atas waktunya."];
const times = ["hari ini", "sekarang", "sebelum pukul 18.00", "dalam 30 menit", "malam ini", "sebelum batas waktu"];
const amounts = ["Rp150.000", "Rp350.000", "Rp500.000", "Rp1.250.000", "Rp2.500.000", "Rp5.000.000"];

const definitions = {
  "Aman": {
    dasar: "ham", subtype: ["percakapan_harian", "undangan_aman", "informasi_resmi"],
    templates: [
      "Besok rapat kelompok dimulai pukul {hour} di ruang {room}.",
      "Kami mengundang Anda ke pernikahan keluarga kami pada {day}. Undangan berupa PDF, tidak perlu memasang aplikasi.",
      "Foto undangan pernikahan sudah saya kirim dalam format JPG. Sampai jumpa di acara ya.",
      "Tolong beli makan siang saat pulang dari kampus, nanti saya ganti.",
      "Jadwal konsultasi dipindah ke {day} pukul {hour} melalui ruang kelas resmi.",
      "Paket sudah diterima oleh satpam. Silakan diambil tanpa biaya tambahan.",
      "Terima kasih sudah hadir di acara keluarga kemarin, foto ada di album bersama.",
      "Pengumuman kampus dapat dilihat melalui portal akademik resmi.",
      "Aku sudah sampai rumah. Kabari kalau kamu juga sudah sampai dengan aman.",
      "Undangan rapat RT terlampir sebagai dokumen PDF dari pengurus yang kamu kenal.",
    ]
  },
  "Phishing/Link Berbahaya": {
    dasar: "spam", subtype: ["undangan_apk", "paket_apk", "tautan_login_palsu"],
    templates: [
      "Kami mengundang Anda ke pesta pernikahan. Buka Foto Undangan_{id}.apk untuk info lengkapnya.",
      "Kami lampirkan Undangan_Digital_Pernikahan_{id}.apk. Mohon diunduh untuk melihat peta lokasi.",
      "Detail waktu dan lokasi pernikahan ada di Undangan Pernikahan {id}.apk, silakan buka {time}.",
      "Paket Anda tertahan. Download aplikasi Cek_Resi_{id}.apk untuk memilih jadwal antar.",
      "Akun bank akan dinonaktifkan. Verifikasi melalui https://bank-verifikasi-{id}.invalid.",
      "Tagihan belum dibayar. Klik tautan [tautan-palsu-{id}] untuk menghindari denda.",
      "Buka file Galeri_Pernikahan_{id}.apk agar foto dan alamat gedung terlihat.",
      "Hadiah pelanggan menunggu. Pasang Bonus_Resmi_{id}.apk untuk klaim.",
      "Undangan resmi elektronik tersedia melalui link http://undangan-{id}.invalid.",
      "Perbarui data akun melalui halaman login https://akun-aman-{id}.invalid {time}.",
    ]
  },
  "Social Engineering": {
    dasar: "spam", subtype: ["permintaan_otp", "penyamaran_petugas", "ancaman_akun"],
    templates: [
      "Saya petugas bank. Sebutkan OTP yang baru masuk agar rekening tidak diblokir {time}.",
      "Admin layanan membutuhkan PIN Anda untuk membatalkan transaksi {amount}.",
      "Nomor Anda bermasalah. Kirim kode verifikasi kepada petugas ini {time}.",
      "Saya dari kantor pusat, mohon konfirmasi password untuk pemeriksaan keamanan.",
      "Atasan meminta transfer darurat {amount}; jangan hubungi siapa pun dulu.",
      "Akun akan dinonaktifkan bila Anda tidak membalas dengan OTP {time}.",
      "Petugas pajak meminta data rekening dan PIN untuk pengembalian dana.",
      "Saya keluarga Anda memakai nomor baru. Tolong transfer {amount} karena sedang darurat.",
      "Customer service meminta foto kartu dan kode rahasia untuk membuka blokir.",
      "Pihak berwenang mengancam denda bila data pribadi tidak dikirim {time}.",
    ]
  },
  "Penipuan Investasi": {
    dasar: "spam", subtype: ["profit_pasti", "trading_palsu", "deposit_awal"],
    templates: [
      "Investasi eksklusif menjanjikan profit {percent}% tanpa risiko. Deposit mulai {amount}.",
      "Gabung grup trading kami, modal {amount} dijamin berlipat dalam {days} hari.",
      "Kesempatan cuan pasti {percent}% per minggu, transfer modal {time}.",
      "Robot trading legal menjamin return tetap. Buka akun dengan setoran {amount}.",
      "Proyek kripto rahasia akan naik {percent}%. Jangan lewatkan penawaran {time}.",
      "Investasi kebun digital memberi bonus anggota dan keuntungan tanpa rugi.",
      "Dana Anda akan dikelola profesional dengan hasil pasti {percent}% per bulan.",
      "Paket investasi VIP tersisa satu slot. Kirim {amount} untuk mengamankan posisi.",
      "Bisnis passive income tanpa kerja, modal kembali dalam {days} hari.",
      "Bukti profit sudah banyak. Transfer dana awal agar akun investasi diaktifkan.",
    ]
  },
  "Penipuan Rekrutmen": {
    dasar: "spam", subtype: ["biaya_administrasi", "tugas_like", "hrd_palsu"],
    templates: [
      "HRD membuka lowongan kerja. Bayar biaya administrasi {amount} sebelum interview.",
      "Anda diterima tanpa tes. Transfer biaya seragam {amount} {time}.",
      "Kerja paruh waktu dari rumah, tugas memberi like dengan deposit awal {amount}.",
      "Undangan interview dari perusahaan besar, beli tiket melalui agen yang kami tunjuk.",
      "Lowongan staf administrasi bergaji tinggi. Kirim PIN dan data rekening untuk payroll.",
      "Rekrutmen resmi tanpa wawancara, bayar pelatihan wajib sebesar {amount}.",
      "Tugas online mudah menghasilkan komisi. Top up saldo agar tugas berikutnya terbuka.",
      "HRD meminta pembayaran medical check-up ke rekening pribadi {time}.",
      "Posisi terbatas, amankan kursi kerja dengan transfer {amount}.",
      "Penerimaan pegawai kilat. Rahasiakan proses dan lunasi biaya dokumen.",
    ]
  },
  "Penipuan Romansa": {
    dasar: "spam", subtype: ["pinjaman_pasangan", "hadiah_tertahan", "darurat_palsu"],
    templates: [
      "Sayang, aku sedang darurat di luar kota. Tolong kirim uang {amount} {time}.",
      "Aku serius ingin menikah denganmu, tetapi paket hadiahku tertahan dan perlu biaya {amount}.",
      "Setelah semua obrolan kita, buktikan kepercayaanmu dengan membantu transfer {amount}.",
      "Aku bekerja di luar negeri dan akan pulang menemuimu. Bayarkan bea paket hadiah dulu.",
      "Cintaku, rekeningku diblokir. Pinjamkan {amount}, nanti langsung kuganti.",
      "Jangan beri tahu keluargamu tentang hubungan kita. Aku butuh bantuan dana {time}.",
      "Aku ingin membangun masa depan bersama, kirim modal kecil untuk usaha kita.",
      "Hadiah pernikahan untukmu tertahan di bea cukai. Bayar tagihannya agar dikirim.",
      "Aku kehilangan dompet saat perjalanan menemuimu. Tolong transfer {amount}.",
      "Kita sudah dekat lama. Tolong bantu biaya pengobatan keluargaku sebesar {amount}.",
    ]
  }
};

const categoryCodes = {
  "Aman": "AMN", "Phishing/Link Berbahaya": "PHI", "Social Engineering": "SOC",
  "Penipuan Investasi": "INV", "Penipuan Rekrutmen": "REK", "Penipuan Romansa": "ROM",
};

const fill = (template, id) => template
  .replaceAll("{id}", String(id).padStart(4, "0"))
  .replaceAll("{time}", pick(times)).replaceAll("{amount}", pick(amounts))
  .replaceAll("{percent}", String(pick([20, 25, 30, 40, 50, 75])))
  .replaceAll("{days}", String(pick([2, 3, 5, 7, 10])))
  .replaceAll("{hour}", pick(["08.00", "09.30", "13.00", "15.30", "19.00"]))
  .replaceAll("{room}", pick(["A1", "B3", "C2", "laboratorium", "aula"]))
  .replaceAll("{day}", pick(["Senin", "Rabu", "Sabtu", "minggu depan"]));

const rows = [];
for (const [category, config] of Object.entries(definitions)) {
  const seen = new Set();
  while (seen.size < 500) {
    const id = seen.size + 1;
    const templateId = Math.floor(random() * config.templates.length);
    const message = `${pick(openings)}, ${fill(config.templates[templateId], id)} ${pick(closings)}`;
    if (seen.has(message)) continue;
    seen.add(message);
    rows.push({
      Kategori: config.dasar, Pesan: message, Kategori_NusaGuard: category,
      Subtipe: config.subtype[Math.min(Math.floor(templateId / 4), config.subtype.length - 1)], Provenance: "synthetic_template_v1",
      Synthetic: true, Reviewed: false, Template_ID: `${categoryCodes[category]}-${templateId + 1}`
    });
  }
}

for (let i = rows.length - 1; i > 0; i--) {
  const j = Math.floor(random() * (i + 1));
  [rows[i], rows[j]] = [rows[j], rows[i]];
}

const headers = Object.keys(rows[0]);
const quote = (value) => `"${String(value).replaceAll('"', '""')}"`;
const toCsv = (data) => [headers.map(quote).join(","), ...data.map(row => headers.map(key => quote(row[key])).join(","))].join("\n") + "\n";
const csv = toCsv(rows);
const output = path.resolve("dataset/processed/nusaguard_balanced_synthetic.csv");
await fs.writeFile(output, csv, "utf8");

const splits = { train: [], val: [], test: [] };
for (const category of Object.keys(definitions)) {
  const categoryRows = rows.filter(row => row.Kategori_NusaGuard === category);
  splits.train.push(...categoryRows.slice(0, 350));
  splits.val.push(...categoryRows.slice(350, 425));
  splits.test.push(...categoryRows.slice(425, 500));
}
for (const [name, data] of Object.entries(splits)) {
  for (let i = data.length - 1; i > 0; i--) {
    const j = Math.floor(random() * (i + 1));
    [data[i], data[j]] = [data[j], data[i]];
  }
  await fs.writeFile(path.resolve(`dataset/training/${name}.csv`), toCsv(data), "utf8");
}
console.log(JSON.stringify({ output, rows: rows.length, seed, splits: Object.fromEntries(Object.entries(splits).map(([name, data]) => [name, data.length])) }, null, 2));
