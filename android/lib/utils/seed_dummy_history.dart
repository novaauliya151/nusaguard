import '../models/history_entry.dart';
import '../models/analyze_result.dart';
import '../services/history_service.dart';

Future<void> seedDummyHistory() async {
  final now = DateTime.now();

  final entries = <HistoryEntry>[
    HistoryEntry(
      message:
          'Halo, saya petugas BRI. Rekening Anda terdeteksi aktivitas mencurigakan. Segera konfirmasi OTP yang masuk atau rekening diblokir permanen',
      result: AnalyzeResult(
        kategoriDasar: 'Social Engineering',
        kategoriNusaGuard: 'Social Engineering',
        riskLevel: 'HIGH',
        riskScore: 94,
        confidence: 88,
        nseaeScores: NseaeScores(
          urgency: 85,
          authority: 82,
          fear: 91,
          reward: 0,
          impersonation: 74,
          credentialRequest: 100,
        ),
        explanation:
            'Pesan ini menggunakan identitas palsu sebagai petugas bank (impersonation), menciptakan rasa takut rekening diblokir (fear), mendesak korban bertindak cepat (urgency), dan meminta kredensial sensitif berupa OTP (credentialRequest).',
        recommendedAction:
            'Jangan berikan OTP kepada siapapun. Bank tidak pernah meminta OTP via telepon/WA. Hubungi call center resmi bank untuk verifikasi.',
      ),
      source: HistorySource.notification,
      timestamp: now.subtract(const Duration(hours: 2)),
    ),
    HistoryEntry(
      message:
          'Kak, ada lowongan kerja online, komisi Rp500rb/hari. Daftar dulu ya kak, transfer deposit Rp200rb untuk aktivasi akun.',
      result: AnalyzeResult(
        kategoriDasar: 'Penipuan Rekrutmen',
        kategoriNusaGuard: 'Penipuan Rekrutmen',
        riskLevel: 'HIGH',
        riskScore: 87,
        confidence: 79,
        nseaeScores: NseaeScores(
          urgency: 40,
          authority: 20,
          fear: 15,
          reward: 78,
          impersonation: 30,
          credentialRequest: 10,
        ),
        explanation:
            'Pesan menawarkan imbalan besar dengan upaya minim (reward), meminta uang muka sebagai deposit (credentialRequest finansial), dan menggunakan tone kasual untuk menurunkan keewaspadaan.',
        recommendedAction:
            'Lowongan kerja legit tidak meminta deposit/uang muka. Verifikasi perusahaan melalui situs resmi. Laporkan ke platform lowongan kerja jika ditemukan.',
      ),
      source: HistorySource.manual,
      timestamp: now.subtract(const Duration(hours: 5)),
    ),
    HistoryEntry(
      message:
          'Hai, jadwal pertemuan kita besok jam 10 ya. Jangan lupa bawa dokumen yang sudah kita bicarakan minggu lalu.',
      result: AnalyzeResult(
        kategoriDasar: 'Aman',
        kategoriNusaGuard: 'Aman',
        riskLevel: 'LOW',
        riskScore: 5,
        confidence: 92,
        nseaeScores: NseaeScores(
          urgency: 0,
          authority: 0,
          fear: 0,
          reward: 0,
          impersonation: 0,
          credentialRequest: 0,
        ),
        explanation:
            'Pesan ini tidak menunjukkan tanda-tanda manipulasi psikologis yang signifikan. Komunikasi normal antar kenal.',
        recommendedAction:
            'Tidak ada tindakan khusus diperlukan. Lanjutkan komunikasi seperti biasa.',
      ),
      source: HistorySource.manual,
      timestamp: now.subtract(const Duration(hours: 20)),
    ),
    HistoryEntry(
      message:
          'Pembayaran tagihan PLN Anda Rp2.500.000 belum lunas. Bayar sekarang via link: bit.ly/pln-bayar-abc123 agar tidak diputus.',
      result: AnalyzeResult(
        kategoriDasar: 'Phishing/Link Berbahaya',
        kategoriNusaGuard: 'Phishing/Link Berbahaya',
        riskLevel: 'HIGH',
        riskScore: 91,
        confidence: 85,
        nseaeScores: NseaeScores(
          urgency: 88,
          authority: 75,
          fear: 82,
          reward: 0,
          impersonation: 70,
          credentialRequest: 90,
        ),
        explanation:
            'Pesan mengatasnamakan PLN (impersonation), menggunakan ancaman pemutusan layanan (fear), mendesak pembayaran segera (urgency), dan mengarahkan ke link mencurigakan bit.ly (credentialRequest/phishing).',
        recommendedAction:
            'Jangan klik link dari WA. Cek tagihan via aplikasi PLN Mobile resmi atau web pln.co.id. Laporkan nomor pengirim ke 110/122.',
      ),
      source: HistorySource.notification,
      timestamp: now.subtract(const Duration(hours: 30)),
    ),
    HistoryEntry(
      message:
          'Investasi emas digital return 15%/bulan, aman & terjamin OJK. Modal minimal Rp1jt. Daftar lewat link ini: wa.me/invest-emas-xyz. Slot terbatas!',
      result: AnalyzeResult(
        kategoriDasar: 'Penipuan Investasi',
        kategoriNusaGuard: 'Penipuan Investasi',
        riskLevel: 'HIGH',
        riskScore: 89,
        confidence: 82,
        nseaeScores: NseaeScores(
          urgency: 65,
          authority: 60,
          fear: 20,
          reward: 85,
          impersonation: 55,
          credentialRequest: 40,
        ),
        explanation:
            'Menjanjikan return tidak wajar (reward), mengklaim terjamin OJK tanpa bukti (authority/impersonation), menciptakan FOMO dengan "slot terbatas" (urgency), dan mengarahkan ke link afiliasi.',
        recommendedAction:
            'Investasi legal butuh izin OJK yang bisa diverifikasi di ojk.go.id. Return 15%/bulan tidak realistis. Jangan transfer ke rekening pribadi.',
      ),
      source: HistorySource.manual,
      timestamp: now.subtract(const Duration(hours: 50)),
    ),
    HistoryEntry(
      message:
          'Sayang, aku butuh bantuan dong. Dompetku kena curian di Bandung, kirim uang ke rekening ini dulu ya: 1234567890 BCA. Besok aku balikin.',
      result: AnalyzeResult(
        kategoriDasar: 'Penipuan Romansa',
        kategoriNusaGuard: 'Penipuan Romansa',
        riskLevel: 'HIGH',
        riskScore: 83,
        confidence: 77,
        nseaeScores: NseaeScores(
          urgency: 78,
          authority: 10,
          fear: 70,
          reward: 0,
          impersonation: 85,
          credentialRequest: 60,
        ),
        explanation:
            'Memanfaatkan hubungan emosional (impersonation sebagai pasangan), menciptakan darurat palsu (urgency/fear), dan meminta transfer uang ke rekening pribadi (credentialRequest finansial).',
        recommendedAction:
            'Verifikasi via video call langsung. Jangan kirim uang ke orang yang baru kenal online. Waspadai cerita darurat mendadak meminta dana.',
      ),
      source: HistorySource.notification,
      timestamp: now.subtract(const Duration(hours: 65)),
    ),
    HistoryEntry(
      message:
          'Selamat! Anda memenangkan undian Promo Akhir Tahun Shopee. Hadiah: iPhone 15 Pro + Rp10jt. Klaim di: shopee-promo.xyz/claim?id=12345',
      result: AnalyzeResult(
        kategoriDasar: 'Phishing/Link Berbahaya',
        kategoriNusaGuard: 'Phishing/Link Berbahaya',
        riskLevel: 'HIGH',
        riskScore: 92,
        confidence: 90,
        nseaeScores: NseaeScores(
          urgency: 70,
          authority: 65,
          fear: 10,
          reward: 95,
          impersonation: 80,
          credentialRequest: 85,
        ),
        explanation:
            'Mengatasnamakan brand besar (impersonation), menawarkan hadiah mahal gratis (reward), menggunakan domain tidak resmi shopee-promo.xyz (credentialRequest/phishing), dan mendesak klaim segera.',
        recommendedAction:
            'Shopee tidak mengirim link hadiah via WA pribadi. Cek promo resmi di aplikasi Shopee. Jangan masukan data pribadi di link mencurigakan.',
      ),
      source: HistorySource.manual,
      timestamp: now.subtract(const Duration(hours: 80)),
    ),
    HistoryEntry(
      message:
          'Pak, ini Bu Siti dari Koperasi Pegawai. Dana bantuan sosial Rp3jt sudah cair. Verifikasi nomor rekening & OTP ya pak supaya masuk.',
      result: AnalyzeResult(
        kategoriDasar: 'Social Engineering',
        kategoriNusaGuard: 'Social Engineering',
        riskLevel: 'HIGH',
        riskScore: 88,
        confidence: 81,
        nseaeScores: NseaeScores(
          urgency: 72,
          authority: 78,
          fear: 40,
          reward: 60,
          impersonation: 82,
          credentialRequest: 95,
        ),
        explanation:
            'Mengatasnamakan pejabat/opk (impersonation & authority), menawarkan dana gratis (reward), dan meminta verifikasi rekening serta OTP (credentialRequest) - modus klasik penipuan bantuan sosial.',
        recommendedAction:
            'Koperasi/lembaga resmi tidak meminta OTP. Verifikasi info bantuan sosial via laman resmi kemensos.go.id atau RT/RW setempat. Jangan berikan OTP.',
      ),
      source: HistorySource.notification,
      timestamp: now.subtract(const Duration(hours: 100)),
    ),
  ];

  for (final entry in entries) {
    await HistoryService.add(entry);
  }
}