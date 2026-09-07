"use client";
import { useEffect, useState } from "react";
import type { AnalyzeResponse } from "./types";
import LogoNusaGuard from "../components/logo_nusaguard";
import styles from "./home.module.css";
import extras from "./home-extras.module.css";
const API = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";
const riskLabels = { LOW: "Rendah", MEDIUM: "Sedang", HIGH: "Tinggi" } as const;
const reasonLabels: Record<string, string> = {
  urgency: "Pesan mendorong kamu untuk bertindak terburu-buru.",
  authority: "Pengirim mengatasnamakan lembaga atau pihak berwenang.",
  fear: "Pesan menggunakan ancaman atau membuat penerima merasa takut.",
  reward: "Pesan menawarkan hadiah atau keuntungan yang perlu diwaspadai.",
  impersonation: "Ada tanda bahwa pengirim mungkin menyamar sebagai orang lain.",
  credential_request: "Pesan meminta data rahasia atau informasi pribadi.",
};
function riskLabel(level: AnalyzeResponse["risk_level"]) {
  return riskLabels[level];
}
function resultHeading(result: AnalyzeResponse) {
  return result.category === "Aman"
    ? "Tidak ditemukan tanda penipuan yang kuat"
    : `Pesan terindikasi ${result.category}`;
}
function resultSummary(result: AnalyzeResponse) {
  if (result.category === "Aman")
    return "Pesan ini terlihat aman berdasarkan pemeriksaan saat ini. Tetap pastikan identitas pengirim sebelum membagikan data pribadi.";
  if (result.risk_level === "HIGH")
    return "Pesan ini memiliki beberapa tanda berbahaya. Jangan ikuti permintaannya sebelum memastikan kebenaran pengirim.";
  if (result.risk_level === "MEDIUM")
    return "Pesan ini memiliki tanda yang perlu diperiksa lebih lanjut. Jangan terburu-buru mengambil tindakan.";
  return "Risikonya terlihat rendah, tetapi tetap periksa pengirim dan jangan membagikan informasi rahasia.";
}
function detectedReasons(result: AnalyzeResponse) {
  return result.detected_patterns
    .map(({ pattern }) => reasonLabels[pattern])
    .filter((reason): reason is string => Boolean(reason));
}
const categories = [
  ["01", "Phishing", "Tautan, situs, dan APK yang menyamar sebagai layanan tepercaya."],
  ["02", "Social engineering", "Manipulasi psikologis untuk memperoleh kredensial atau uang."],
  ["03", "Investasi", "Janji keuntungan pasti, besar, dan mendesak."],
  ["04", "Rekrutmen", "Lowongan palsu yang meminta biaya atau data sensitif."],
  ["05", "Romansa", "Kedekatan emosional yang berujung permintaan uang."],
];
type Stats = {
  total_analyzed: number;
  month_total: number;
  top_category_this_month: string | null;
};
export default function Home() {
  const [message, setMessage] = useState(""),
    [result, setResult] = useState<AnalyzeResponse | null>(null),
    [loading, setLoading] = useState(false),
    [error, setError] = useState<string | null>(null),
    [stats, setStats] = useState<Stats | null>(null),
    [navOpen, setNavOpen] = useState(false);
  useEffect(() => {
    fetch(`${API}/api/stats`)
      .then((r) => (r.ok ? r.json() : null))
      .then(setStats)
      .catch(() => setStats(null));
  }, []);
  useEffect(() => {
    if (!navOpen) return;
    const close = (event: KeyboardEvent) => {
      if (event.key === "Escape") setNavOpen(false);
    };
    document.addEventListener("keydown", close);
    const previous = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    return () => {
      document.removeEventListener("keydown", close);
      document.body.style.overflow = previous;
    };
  }, [navOpen]);
  async function analyze() {
    if (!message.trim()) return;
    setLoading(true);
    setError(null);
    setResult(null);
    try {
      const r = await fetch(`${API}/api/analyze`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text: message, source: "manual_web" }),
      });
      if (!r.ok) throw new Error();
      setResult(await r.json());
    } catch {
      setError("API belum dapat dijangkau. Periksa status backend dan NEXT_PUBLIC_API_URL.");
    } finally {
      setLoading(false);
    }
  }
  const closeNav = () => setNavOpen(false);
  return (
    <div className={styles.shell}>
      <header className={styles.header}>
        <a className={styles.brand} href="#top" onClick={closeNav}>
          <LogoNusaGuard />
          NusaGuard
        </a>
        <button
          className={styles.navToggle}
          type="button"
          aria-label={navOpen ? "Tutup menu navigasi" : "Buka menu navigasi"}
          aria-expanded={navOpen}
          aria-controls="home-navigation"
          onClick={() => setNavOpen((open) => !open)}
        >
          <span />
          <span />
          <span />
        </button>
        <nav id="home-navigation" className={`${styles.nav} ${navOpen ? styles.navOpen : ""}`}>
          <a href="#cara-kerja" onClick={closeNav}>
            Cara kerja
          </a>
          <a href="#analisis" onClick={closeNav}>
            Analisis
          </a>
          <a href="/statistics" onClick={closeNav}>
            Statistik
          </a>
          <a href="/education" onClick={closeNav}>
            Edukasi
          </a>
          <a href="/dataset" onClick={closeNav}>
            Dataset
          </a>
          <a className={extras.register} href="/register" onClick={closeNav}>
            Daftar
          </a>
          <a className={styles.login} href="/login" onClick={closeNav}>
            Masuk
          </a>
        </nav>
      </header>
      <button
        className={`${styles.navBackdrop} ${navOpen ? styles.navBackdropOpen : ""}`}
        type="button"
        aria-label="Tutup menu navigasi"
        onClick={closeNav}
      />
      <main id="top">
        <section className={styles.hero}>
          <div>
            <p className={styles.eyebrow}>AI ANTI-PENIPUAN BERBAHASA INDONESIA</p>
            <h1>
              Jangan buru-buru.
              <br />
              <em>Periksa dulu.</em>
            </h1>
            <p className={styles.lead}>
              NusaGuard membaca pola manipulasi dalam pesan mencurigakan, menjelaskan risikonya, dan
              memberi langkah aman sebelum kamu klik, membagikan data, atau transfer.
            </p>
            <div className={styles.heroActions}>
              <a className={styles.primary} href="#analisis">
                Periksa pesan sekarang
              </a>
              <a className={styles.secondary} href="/education">
                Pelajari modus
              </a>
            </div>
            <div className={styles.trust}>
              <span>Analisis tanpa login</span>
              <span>Teks tidak disimpan</span>
              <span>Penjelasan transparan</span>
            </div>
          </div>
          <div className={styles.visual} aria-hidden>
            <div className={`${styles.signal} ${styles.one}`}>
              <span className={styles.dot} />6 indikator aktif<b>N-SEAE</b>
            </div>
            <div className={styles.shield}>N</div>
            <div className={`${styles.signal} ${styles.two}`}>
              <span className={styles.dot} />
              Mesin klasifikasi<b>IndoBERT + fusion</b>
            </div>
          </div>
        </section>
        <section className={styles.stats}>
          <article>
            <span>TOTAL PESAN DIANALISIS</span>
            <strong>{stats?.total_analyzed.toLocaleString("id-ID") ?? "—"}</strong>
            <p>agregat anonim</p>
          </article>
          <article>
            <span>ANALISIS BULAN INI</span>
            <strong>{stats?.month_total.toLocaleString("id-ID") ?? "—"}</strong>
            <p>terus diperbarui</p>
          </article>
          <article>
            <span>MODUS TERBANYAK BULAN INI</span>
            <strong>{stats?.top_category_this_month ?? "Belum ada data"}</strong>
            <p>
              <a href="/statistics">Lihat statistik lengkap</a>
            </p>
          </article>
        </section>
        <section id="cara-kerja" className={styles.flow}>
          <div className={styles.title}>
            <div>
              <p className={styles.eyebrow}>PERLINDUNGAN DALAM TIGA LANGKAH</p>
              <h2>Dari pesan mencurigakan ke keputusan yang lebih aman.</h2>
            </div>
            <p>
              NusaGuard dirancang agar dapat digunakan masyarakat tanpa pengetahuan teknis dan tanpa
              menyerahkan privasi.
            </p>
          </div>
          <div className={styles.steps}>
            <article>
              <small>01</small>
              <h3>Tempel pesannya</h3>
              <p>Salin pesan WhatsApp, SMS, atau chat yang terasa mencurigakan.</p>
            </article>
            <article>
              <small>02</small>
              <h3>Baca polanya</h3>
              <p>IndoBERT dan N-SEAE menilai kategori serta enam sinyal manipulasi.</p>
            </article>
            <article>
              <small>03</small>
              <h3>Ambil langkah aman</h3>
              <p>Dapatkan alasan, tingkat risiko, dan rekomendasi tindakan yang jelas.</p>
            </article>
          </div>
        </section>
        <section id="analisis" className={styles.analyzer}>
          <div className={styles.title}>
            <div>
              <p className={styles.eyebrow}>PEMERIKSAAN EPHEMERAL</p>
              <h2>
                Tempel pesan.
                <br />
                Kami bantu membacanya.
              </h2>
            </div>
            <p>
              Isi pesan hanya diproses untuk permintaan ini dan tidak dimasukkan ke histori atau
              dataset secara otomatis.
            </p>
          </div>
          <div className={styles.workspace}>
            <div className={styles.card}>
              <div className={styles.cardHead}>
                <label htmlFor="message">ISI PESAN WHATSAPP / SMS</label>
                <span>MAKS. 5.000 KARAKTER</span>
              </div>
              <textarea
                id="message"
                maxLength={5000}
                value={message}
                onChange={(e) => setMessage(e.target.value)}
                placeholder="Contoh: Selamat! Akun Anda mendapat hadiah. Segera kirim OTP untuk verifikasi..."
              />
              <div className={styles.cardFoot}>
                <span>{message.length}/5000</span>
                <button
                  className={styles.primary}
                  onClick={analyze}
                  disabled={loading || !message.trim()}
                >
                  {loading ? "Menganalisis…" : "Analisis pesan"}
                </button>
              </div>
              {error && (
                <p className={styles.error} role="alert">
                  {error}
                </p>
              )}
            </div>
            <div
              className={`${styles.card} ${result ? (result.risk_level === "HIGH" ? styles.riskHigh : result.risk_level === "MEDIUM" ? styles.riskMedium : styles.riskLow) : ""}`}
            >
              {!result ? (
                <div className={styles.empty}>
                  <div className={styles.radar}>⌁</div>
                  <h3>Hasil analisis muncul di sini</h3>
                  <p>Enam indikator manipulasi diperiksa secara transparan.</p>
                </div>
              ) : (
                <>
                  <div className={styles.riskHead}>
                    <div>
                      <span className={styles.badge}>TINGKAT RISIKO</span>
                      <h3>{riskLabel(result.risk_level)}</h3>
                    </div>
                    <div className={styles.score}>
                      {Math.round(result.risk_score * 100)}%<small>perkiraan tingkat bahaya</small>
                    </div>
                  </div>
                  <h4 className={styles.resultHeading}>{resultHeading(result)}</h4>
                  <p className={styles.resultText}>{resultSummary(result)}</p>
                  <div className={styles.riskScale} aria-label="Panduan tingkat risiko">
                    <span>
                      Rendah
                      <br />
                      Tetap waspada
                    </span>
                    <span>
                      Sedang
                      <br />
                      Periksa kembali
                    </span>
                    <span>
                      Tinggi
                      <br />
                      Jangan ditindaklanjuti
                    </span>
                  </div>
                  {detectedReasons(result).length > 0 && (
                    <div className={styles.reasons}>
                      <b>Mengapa hasilnya seperti ini?</b>
                      <ul>
                        {detectedReasons(result).map((reason) => (
                          <li key={reason}>{reason}</li>
                        ))}
                      </ul>
                    </div>
                  )}
                  <div className={styles.recommend}>
                    <b>Yang sebaiknya kamu lakukan</b>
                    <p>{result.recommendation}</p>
                  </div>
                </>
              )}
            </div>
          </div>
        </section>
        <section className={styles.categories}>
          <div className={styles.title}>
            <div>
              <p className={styles.eyebrow}>LIMA MODUS UTAMA</p>
              <h2>Kenali pola sebelum bertindak.</h2>
            </div>
            <p>
              Setiap kategori menghasilkan penjelasan dan rekomendasi yang berbeda agar pengguna
              memahami konteks risikonya.
            </p>
          </div>
          <div className={styles.categoryGrid}>
            {categories.map(([n, title, text]) => (
              <article key={n}>
                <span>{n}</span>
                <h3>{title}</h3>
                <p>{text}</p>
              </article>
            ))}
          </div>
        </section>
        <section className={styles.platform}>
          <div>
            <p className={styles.eyebrow}>MESIN YANG DAPAT DIJELASKAN</p>
            <h2>
              Bahasa dipahami.
              <br />
              Manipulasi dibedah.
            </h2>
            <p>
              IndoBERT mempelajari konteks bahasa Indonesia. N-SEAE memperlihatkan sinyal psikologis
              yang memengaruhi risiko, lalu safety guard menangani indikator kritis seperti APK dan
              permintaan kredensial.
            </p>
          </div>
          <div className={styles.layers}>
            <article>
              <span>01</span>
              <div>
                <b>IndoBERT</b>
                <small>Klasifikasi konteks ke enam kategori</small>
              </div>
            </article>
            <article>
              <span>02</span>
              <div>
                <b>N-SEAE</b>
                <small>Urgensi, otoritas, ketakutan, imbalan, penyamaran, dan data</small>
              </div>
            </article>
            <article>
              <span>03</span>
              <div>
                <b>Fusion & safety guard</b>
                <small>Menggabungkan probabilitas dan indikator kritis</small>
              </div>
            </article>
          </div>
        </section>
        <section className={styles.community}>
          <div className={styles.title}>
            <div>
              <p className={styles.eyebrow}>PENGETAHUAN YANG KEMBALI KE PUBLIK</p>
              <h2>Satu ekosistem perlindungan.</h2>
            </div>
          </div>
          <div className={styles.communityGrid}>
            <article>
              <span>EDUKASI DINAMIS</span>
              <h3>Kenali modus terbaru</h3>
              <p>Konten awal tersedia dan dapat diperbarui admin berdasarkan pola yang ditinjau.</p>
              <a href="/education">Buka edukasi</a>
            </article>
            <article>
              <span>LAPORAN SUKARELA</span>
              <h3>Bantu lindungi yang lain</h3>
              <p>Kirim contoh pesan dengan consent tanpa menyertakan identitas pribadi.</p>
              <a href="/report">Buat laporan</a>
            </article>
            <article>
              <span>DATASET PUBLIK</span>
              <h3>Transparan dan anonim</h3>
              <p>Akses laporan yang telah disetujui, dimoderasi, dan dianonimkan.</p>
              <a href="/dataset">Lihat dataset</a>
            </article>
          </div>
        </section>
        <section className={styles.privacy}>
          <p className={styles.eyebrow}>PRIVASI SEJAK AWAL</p>
          <h2>
            Pesanmu lewat.
            <br />
            Bukan menetap.
          </h2>
          <div className={styles.privacyGrid}>
            <article>
              <span>01</span>
              <div>
                <h3>Analisis tidak menetap</h3>
                <p>Isi pesan diproses secara ephemeral dan tidak otomatis masuk ke riwayat.</p>
              </div>
            </article>
            <article>
              <span>02</span>
              <div>
                <h3>Persetujuan tetap utama</h3>
                <p>Laporan hanya disimpan setelah pengguna memberikan persetujuan eksplisit.</p>
              </div>
            </article>
            <article>
              <span>03</span>
              <div>
                <h3>Akses perangkat dibatasi</h3>
                <p>NusaGuard tidak membaca kontak, database WhatsApp, atau percakapan perangkat.</p>
              </div>
            </article>
          </div>
        </section>
      </main>
      <footer className={styles.footer}>
        <span>© NusaGuard · Periksa sebelum percaya</span>
        <span>IndoBERT + N-SEAE · Privacy-first</span>
      </footer>
    </div>
  );
}
