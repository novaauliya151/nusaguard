import 'package:flutter/material.dart';
import '../models/analyze_result.dart';
import '../models/history_entry.dart';
import '../services/analyze_service.dart';
import '../services/history_service.dart';

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
