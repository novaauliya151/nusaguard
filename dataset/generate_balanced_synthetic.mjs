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

// Hard cases manual: pesan pendek/netral dan pola penipuan kontemporer.
// Semua identitas, tautan, nominal, serta dokumen bersifat fiktif dan aman.
const contemporaryHardCases = {
  "Aman": [
    "cobalah ini aja", "oke", "sip makasih", "nanti aku kabari", "sudah sampai belum?",
    "jadi ketemu jam tiga?", "file PDF-nya sudah kukirim", "cek grup kelas ya", "aku lagi di jalan",
    "jangan lupa makan", "boleh minta foto catatan kuliah?", "rapatnya pindah ke ruang B2",
    "paketku sudah sampai tanpa biaya tambahan", "gunakan aplikasi resmi dari Play Store",
    "jangan pernah bagikan OTP atau PIN", "QRIS kasir ini sesuai nama tokonya",
    "informasi beasiswa ada di portal resmi kampus", "undangannya berupa gambar JPG, bukan aplikasi",
    "voice chat WhatsApp tidak otomatis menguras saldo", "kalau ragu hubungi nomor resmi bank"
  ],
  "Phishing/Link Berbahaya": [
    "Surat PHK terbaru ada di lampiran Surat_Pusat.apk, buka sekarang.",
    "Foto paket gagal antar ada di CekPaket.apk.", "Scan barcode ini untuk memperbarui data Dukcapil.",
    "Daftar pemutihan pinjol OJK lewat https://pemutihan-ojk.invalid.",
    "Unduh bukti tilang pada E-Tilang_Resmi.apk.", "Klik https://bansos-verifikasi.invalid untuk pencairan bantuan.",
    "File ZIP foto kegiatan ini harus diekstrak lalu jalankan isinya.",
    "Akun WhatsApp akan ditutup, login ulang di https://wa-pusat.invalid.",
    "QR bantuan pemerintah ini mengarah ke formulir login.", "Invoice pajak terlampir sebagai Tagihan.apk."
  ],
  "Social Engineering": [
    "Saya staf kepala dinas, tolong transfer dana kegiatan ke rekening ini.",
    "Ini nomor baru pimpinan. Rahasiakan dan kirim dana operasional sekarang.",
    "Saya polisi, angkat video call ini agar perkara Anda tidak diproses.",
    "Suara di voice note ini dari atasan, segera kirim uang tanpa konfirmasi.",
    "Petugas Dukcapil meminta foto KTP dan kode OTP untuk pembaruan data.",
    "CS dompet digital meminta Anda membagikan layar dan menyebutkan PIN.",
    "Kurir meminta kode verifikasi yang baru masuk agar paket dapat diserahkan.",
    "Akun anak Anda menghubungi dari nomor baru dan meminta transfer darurat.",
    "Petugas IASC palsu menawarkan pengembalian dana dengan meminta OTP.",
    "Nomor yang memakai foto pejabat meminta sumbangan melalui rekening pribadi."
  ],
  "Penipuan Investasi": [
    "Masuk grup saham VIP, sinyal AI kami menjamin profit 30 persen setiap hari.",
    "Robot trading otomatis tanpa risiko, deposit awal Rp500.000.",
    "Koin baru pasti naik sepuluh kali lipat, transfer sebelum presale ditutup.",
    "Investasi task merchant menjanjikan komisi setelah top up saldo.",
    "Titip dana ke rekening mentor untuk mendapat cuan pasti malam ini.",
    "Aplikasi investasi belum berizin ini menjamin penarikan instan.",
    "Paket staking eksklusif memberi return tetap 20 persen per minggu.",
    "Admin grup meminta pajak pencairan sebelum keuntungan bisa ditarik.",
    "Gunakan akun pinjaman untuk modal trading yang dijamin menang.",
    "Bukti profit selebritas dibuat AI, setor sekarang agar tidak kehabisan slot."
  ],
  "Penipuan Rekrutmen": [
    "Kerja like video dari rumah, top up dulu untuk membuka tugas berikutnya.",
    "Anda diterima magang tanpa wawancara, bayar seragam hari ini.",
    "HRD meminta biaya medical check-up ke rekening pribadi.",
    "Lowongan admin marketplace, gunakan rekening Anda untuk menerima dana pelanggan.",
    "Interview hanya lewat Telegram dan peserta wajib membeli tiket dari agen kami.",
    "Tugas optimasi produk memberi komisi besar setelah deposit.",
    "Penerimaan pegawai BUMN dipercepat jika membayar biaya dokumen.",
    "Recruiter meminta OTP akun pencari kerja untuk verifikasi.",
    "Gaji harian Rp2 juta tanpa pengalaman, klik formulir pribadi ini.",
    "Rahasiakan proses rekrutmen dan transfer uang jaminan posisi."
  ],
  "Penipuan Romansa": [
    "Kita baru kenal, tapi aku sayang kamu. Tolong kirim biaya tiket untuk menemuimu.",
    "Paket hadiah dari luar negeri tertahan bea cukai, bayarkan tagihannya ya sayang.",
    "Jangan cerita keluarga tentang hubungan kita, aku butuh dana darurat.",
    "Aku tentara di luar negeri dan perlu uang agar bisa pulang menikahimu.",
    "Buktikan cintamu dengan membayar biaya rumah sakit keluargaku.",
    "Akun dating-ku bermasalah, kirim uang ke rekening temanku.",
    "Aku ingin masa depan bersama, modal usaha kita transfer hari ini.",
    "Video call-ku rusak, tetapi kirim dulu uang untuk tiket perjalanan.",
    "Hadiah pernikahan kita ditahan kurir dan harus ditebus sekarang.",
    "Setelah semua chat kita, masa kamu tidak percaya untuk meminjamkan uang?"
  ]
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
  for (const [index, message] of contemporaryHardCases[category].entries()) {
    seen.add(message);
    rows.push({
      Kategori: config.dasar, Pesan: message, Kategori_NusaGuard: category,
      Subtipe: "contemporary_hard_case", Provenance: "synthetic_contemporary_v2",
      Synthetic: true, Reviewed: false, Template_ID: `${categoryCodes[category]}-H${index + 1}`
    });
  }
  while (seen.size < 600) {
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
  splits.train.push(...categoryRows.slice(0, 420));
  splits.val.push(...categoryRows.slice(420, 510));
  splits.test.push(...categoryRows.slice(510, 600));
}
for (const [name, data] of Object.entries(splits)) {
  for (let i = data.length - 1; i > 0; i--) {
    const j = Math.floor(random() * (i + 1));
    [data[i], data[j]] = [data[j], data[i]];
  }
  await fs.writeFile(path.resolve(`dataset/training/${name}.csv`), toCsv(data), "utf8");
}
console.log(JSON.stringify({ output, rows: rows.length, seed, splits: Object.fromEntries(Object.entries(splits).map(([name, data]) => [name, data.length])) }, null, 2));

