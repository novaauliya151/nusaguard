import 'package:flutter/material.dart';
import '../models/analyze_result.dart';
import '../models/history_entry.dart';
import '../services/analyze_service.dart';
import '../services/history_service.dart';
import 'dart:convert';
import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;
import '../models/analyze_result.dart';

const _apiUrl = String.fromEnvironment('API_URL', defaultValue: 'http://10.0.2.2:8000');

class HomeScreen extends StatefulWidget {
  const HomeScreen({super.key});

  @override
  State<HomeScreen> createState() => _HomeScreenState();
}

class _HomeScreenState extends State<HomeScreen> {
  final TextEditingController _controller = TextEditingController();
  bool _isLoading = false;
  String? _errorMessage;
  AnalyzeResult? _result;
  final AnalyzeService _analyzeService = AnalyzeService();
  int _requestId = 0;

  Future<void> _handleAnalyze() async {
    final message = _controller.text.trim();
    if (message.isEmpty) return;
    final requestId = ++_requestId;

    setState(() {
      _isLoading = true;
      _errorMessage = null;
      _result = null;
    });

    try {
      final result = await _analyzeService.analyzeMessage(message, source: 'manual');
      if (!mounted || requestId != _requestId) return;
      setState(() => _result = result);

      try {
        await HistoryService.add(
          HistoryEntry(
            message: message,
            result: result,
            source: HistorySource.manual,
          ),
        );
        if (mounted && requestId == _requestId) {
          ScaffoldMessenger.of(context).showSnackBar(
            const SnackBar(content: Text('Hasil tersimpan di Riwayat.')),
          );
        }
      } catch (_) {
        if (mounted && requestId == _requestId) {
          ScaffoldMessenger.of(context).showSnackBar(
            const SnackBar(
              content: Text('Hasil tampil, tetapi gagal disimpan ke Riwayat.'),
            ),
          );
        }
      }
    } catch (e) {
      if (!mounted || requestId != _requestId) return;
      setState(() => _errorMessage = 'Tidak dapat terhubung ke server: $e');
    } finally {
      if (mounted && requestId == _requestId) {
        setState(() => _isLoading = false);
      }
      final r = await http.post(
        Uri.parse('$_apiUrl/api/analyze'),
        headers: {'Content-Type': 'application/json'},
        body: jsonEncode({'message': message, 'source': 'manual'}),
      ).timeout(const Duration(seconds: 60));

      if (r.statusCode == 200) {
        final data = jsonDecode(r.body) as Map<String, dynamic>;
        setState(() => _result = AnalyzeResult.fromJson(data));
      } else {
        setState(() => _errorMessage = 'Gagal menganalisis (status ${r.statusCode}): ${r.body}');
      }
    } catch (e) {
      setState(() => _errorMessage = 'Tidak dapat terhubung ke server: $e');
    } finally {
      setState(() => _isLoading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final scheme = Theme.of(context).colorScheme;

    return Scaffold(
      appBar: AppBar(title: const Text('NusaGuard')),
      body: Padding(
        padding: const EdgeInsets.all(16),
        child: ListView(
          children: [
            TextField(
              controller: _controller,
              maxLines: 5,
              decoration: const InputDecoration(
                border: OutlineInputBorder(),
                hintText: 'Tempel pesan yang mau dicek di sini...',
              ),
            ),
            const SizedBox(height: 12),
            FilledButton.icon(
              onPressed: _isLoading ? null : _handleAnalyze,
              icon: _isLoading
                  ? const SizedBox(
                      height: 18,
                      width: 18,
                      child: CircularProgressIndicator(strokeWidth: 2),
                    )
                  : const Icon(Icons.search),
              label: const Text('Analisis Pesan'),
            ),
            const SizedBox(height: 20),
            if (_errorMessage != null)
              Padding(
                padding: const EdgeInsets.only(bottom: 12),
                child: Text(_errorMessage!, style: TextStyle(color: scheme.error)),
              ),
            if (_result != null) _buildResultCard(_result!, scheme),
          ],
        ),
      ),
    );
  }

  Widget _buildResultCard(AnalyzeResult result, ColorScheme scheme) {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(18),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            _header(result, scheme),
            const SizedBox(height: 16),
            _riskSection(result, scheme),
            const SizedBox(height: 16),
            _explainableSection(result.nseaeScores, scheme),
            _scoreSection(result, scheme),
            const SizedBox(height: 16),
            _nseaeChips(result.nseaeScores),
            const SizedBox(height: 16),
            Text(result.explanation),
            const SizedBox(height: 16),
            _recommendedAction(result.recommendedAction, scheme),
          ],
        ),
      ),
    );
  }

  Widget _header(AnalyzeResult result, ColorScheme scheme) {
    return Row(
      children: [
        Icon(
          result.riskLevel == 'HIGH'
              ? Icons.dangerous_outlined
              : result.riskLevel == 'MEDIUM'
                  ? Icons.warning_amber_outlined
                  : Icons.check_circle_outline,
          color: result.riskLevel == 'HIGH'
              ? scheme.error
              : result.riskLevel == 'MEDIUM'
                  ? scheme.tertiary
                  : scheme.primary,
          size: 32,
        ),
        const SizedBox(width: 12),
        Expanded(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                result.kategoriNusaGuard,
                style: const TextStyle(fontSize: 18, fontWeight: FontWeight.bold),
              ),
              Text(
                _riskLabel(result.riskLevel),
                'Kategori: ${result.kategoriDasar} · Risiko: ${result.riskLevel}',
                style: TextStyle(color: scheme.onSurfaceVariant),
              ),
            ],
          ),
        ),
      ],
    );
  }

  Widget _riskSection(AnalyzeResult result, ColorScheme scheme) {
    final percent = (result.riskScore.clamp(0, 1) * 100).round();
    final color = _riskColor(result.riskLevel, scheme);

    return Container(
      width: double.infinity,
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: color.withValues(alpha: 0.10),
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: color.withValues(alpha: 0.35)),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            '$percent%',
            style: TextStyle(
              fontSize: 34,
              fontWeight: FontWeight.w800,
              color: color,
            ),
          ),
          const SizedBox(height: 2),
          const Text(
            'Perkiraan tingkat bahaya',
            style: TextStyle(fontWeight: FontWeight.w700),
          ),
          const SizedBox(height: 6),
          Text(
            'Semakin tinggi angkanya, semakin banyak tanda bahaya yang ditemukan.',
            style: TextStyle(color: scheme.onSurfaceVariant),
          ),
        ],
      ),
    );
  }

  Widget _explainableSection(NseaeScores scores, ColorScheme scheme) {
    final entries = <String, double>{
      'Ada desakan untuk segera bertindak.': scores.urgency,
      'Pesan mengatasnamakan pihak berwenang.': scores.authority,
      'Pesan menggunakan ancaman atau rasa takut.': scores.fear,
      'Pesan menawarkan hadiah atau keuntungan.': scores.reward,
      'Pengirim mungkin menyamar sebagai orang lain.': scores.impersonation,
      'Pesan meminta data rahasia atau informasi pribadi.':
          scores.credentialRequest,
    };

    final visible = entries.entries.where((e) => e.value > 0).toList();

    return Container(
      width: double.infinity,
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: scheme.surfaceContainerHighest,
        borderRadius: BorderRadius.circular(16),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Row(
            children: [
              Icon(Icons.psychology_alt_outlined, size: 22),
              SizedBox(width: 8),
              Expanded(
                child: Text(
                  'Mengapa hasilnya seperti ini?',
                  style: TextStyle(fontWeight: FontWeight.w700),
                ),
              ),
            ],
          ),
          const SizedBox(height: 10),
          if (visible.isEmpty)
            Text(
              'Tidak ditemukan tanda manipulasi yang kuat.',
              style: TextStyle(color: scheme.onSurfaceVariant),
            )
          else
            ...visible.map(
              (entry) => Padding(
                padding: const EdgeInsets.only(bottom: 8),
                child: Row(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Icon(Icons.check_circle_outline, size: 18, color: scheme.primary),
                    const SizedBox(width: 8),
                    Expanded(child: Text(entry.key)),
                  ],
                ),
              ),
            ),
        ],
      ),
    );
  }

  String _riskLabel(String riskLevel) {
    switch (riskLevel) {
      case 'HIGH':
        return 'Risiko tinggi';
      case 'MEDIUM':
        return 'Risiko sedang';
      default:
        return 'Risiko rendah';
    }
  }

  Color _riskColor(String riskLevel, ColorScheme scheme) {
    switch (riskLevel) {
      case 'HIGH':
        return scheme.error;
      case 'MEDIUM':
        return Colors.orange.shade800;
      default:
        return Colors.green.shade700;
    }
  // CATATAN: risk_score dan confidence dari backend sudah dalam skala
  // 0-100 (bukan 0-1), jadi TIDAK dikali 100 lagi di sini.
  Widget _scoreSection(AnalyzeResult result, ColorScheme scheme) {
    return Row(
      children: [
        _scoreChip('Risiko', result.riskScore, scheme),
        const SizedBox(width: 8),
        _scoreChip('Confidence', result.confidence, scheme),
      ],
    );
  }

  Widget _scoreChip(String label, double value, ColorScheme scheme) {
    final percent = value.round();
    return Expanded(
      child: Container(
        padding: const EdgeInsets.symmetric(vertical: 10, horizontal: 12),
        decoration: BoxDecoration(
          color: scheme.surfaceContainerHighest,
          borderRadius: BorderRadius.circular(12),
        ),
        child: Column(
          children: [
            Text(
              '$percent%',
              style: TextStyle(
                fontSize: 20,
                fontWeight: FontWeight.bold,
                color: scheme.onSurface,
              ),
            ),
            Text(
              label,
              style: TextStyle(fontSize: 12, color: scheme.onSurfaceVariant),
            ),
          ],
        ),
      ),
    );
  }

  // CATATAN: nseae_scores juga skala 0-100, threshold disesuaikan jadi >30
  // (bukan >0.3), dan tidak dikali 100 lagi.
  Widget _nseaeChips(NseaeScores scores) {
    final entries = <String, double>{
      'Urgency': scores.urgency,
      'Authority': scores.authority,
      'Fear': scores.fear,
      'Reward': scores.reward,
      'Impersonation': scores.impersonation,
      'Credential Request': scores.credentialRequest,
    };

    final visible = entries.entries.where((e) => e.value > 30).toList();

    if (visible.isEmpty) return const SizedBox.shrink();

    return Wrap(
      spacing: 8,
      runSpacing: 8,
      children: visible.map((e) {
        final percent = e.value.round();
        return Chip(
          label: Text('${e.key}: $percent%'),
          visualDensity: VisualDensity.compact,
        );
      }).toList(),
    );
  }

  Widget _recommendedAction(String action, ColorScheme scheme) {
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: scheme.primaryContainer,
        borderRadius: BorderRadius.circular(12),
      ),
      child: Row(
        children: [
          Icon(Icons.lightbulb_outline, color: scheme.onPrimaryContainer),
          const SizedBox(width: 8),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  'Yang sebaiknya kamu lakukan',
                  'Saran Tindakan:',
                  style: TextStyle(
                    fontWeight: FontWeight.bold,
                    color: scheme.onPrimaryContainer,
                  ),
                ),
                Text(
                  action,
                  style: TextStyle(color: scheme.onPrimaryContainer),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}
}
