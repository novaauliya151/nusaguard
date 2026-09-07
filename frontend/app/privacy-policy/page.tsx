import Link from "next/link";

export default function PrivacyPolicy() {
  return (
    <main style={{ maxWidth: 900, margin: "0 auto", padding: "70px 24px", lineHeight: 1.75 }}>
      <p style={{ letterSpacing: ".14em", fontSize: 12 }}>KEBIJAKAN PRIVASI</p>
      <h1 style={{ font: "500 clamp(42px, 7vw, 72px) Georgia", margin: "12px 0 28px" }}>
        Privasi pengguna NusaGuard.
      </h1>
      <p>
        NusaGuard memproses teks yang dikirim untuk menghasilkan analisis. Analisis publik tidak
        otomatis menyimpan isi pesan maupun memasukkannya ke dataset.
      </p>
      <h2>Data akun</h2>
      <p>
        Jika pengguna membuat akun, sistem menyimpan nama, email, hash kata sandi, role, status
        akun, serta pengaturan privasi yang diperlukan untuk menyediakan layanan.
      </p>
      <h2>Laporan sukarela</h2>
      <p>
        Laporan hanya disimpan setelah persetujuan eksplisit. Data harus ditinjau, dianonimkan, dan
        disetujui admin sebelum dapat ditampilkan sebagai dataset publik.
      </p>
      <h2>Kontak</h2>
      <p>
        Pertanyaan mengenai privasi dapat dikirim ke{" "}
        <a href="mailto:nusaguard@gmail.com">nusaguard@gmail.com</a>.
      </p>
      <Link href="/">Kembali ke beranda</Link>
    </main>
  );
}
