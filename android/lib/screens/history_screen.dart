import 'package:flutter/material.dart';
import '../models/history_entry.dart';
import '../services/history_service.dart';

class HistoryScreen extends StatefulWidget {
  const HistoryScreen({super.key});

  @override
  State<HistoryScreen> createState() => _HistoryScreenState();
}

class _HistoryScreenState extends State<HistoryScreen> {
  List<HistoryEntry> _entries = [];
  bool _isLoading = true;

  @override
  void initState() {
    super.initState();
    HistoryService.changes.addListener(_loadHistory);
    _loadHistory();
  }

  @override
  void dispose() {
    HistoryService.changes.removeListener(_loadHistory);
    super.dispose();
  }

  Future<void> _loadHistory() async {
    final entries = await HistoryService.getAll();
    if (!mounted) return;
    setState(() {
      _entries = entries;
      _isLoading = false;
    });
  }

  Color _riskColor(String riskLevel) {
    switch (riskLevel) {
      case 'HIGH':
        return Colors.red;
      case 'MEDIUM':
        return Colors.orange;
      default:
        return Colors.green;
    }
  }

  String _formatTimestamp(DateTime dt) {
    final d = dt.day.toString().padLeft(2, '0');
    final m = dt.month.toString().padLeft(2, '0');
    final y = dt.year;
    final h = dt.hour.toString().padLeft(2, '0');
    final min = dt.minute.toString().padLeft(2, '0');
    return '$d/$m/$y $h:$min';
  }

  void _showDetail(HistoryEntry entry) {
    final result = entry.result;
    final scores = result.nseaeScores;
    final scheme = Theme.of(context).colorScheme;

    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      builder: (ctx) => DraggableScrollableSheet(
        initialChildSize: 0.7,
        minChildSize: 0.4,
        maxChildSize: 0.95,
        expand: false,
        builder: (ctx, scrollController) => ListView(
          controller: scrollController,
          padding: const EdgeInsets.all(20),
          children: [
            Center(
              child: Container(
                width: 40,
                height: 4,
                margin: const EdgeInsets.only(bottom: 16),
                decoration: BoxDecoration(
                  color: scheme.onSurfaceVariant.withValues(alpha: 0.3),
                  borderRadius: BorderRadius.circular(2),
                ),
              ),
            ),
            Text(
              result.kategoriNusaGuard,
              style: const TextStyle(fontSize: 20, fontWeight: FontWeight.bold),
            ),
            const SizedBox(height: 4),
            Text(
              _riskLabel(result.riskLevel),
              style: TextStyle(color: scheme.onSurfaceVariant),
            ),
            const SizedBox(height: 16),
            Text(
              entry.message,
              style: TextStyle(
                color: scheme.onSurface,
                fontSize: 14,
              ),
            ),
            const Divider(height: 32),
            _scoreCard('Perkiraan tingkat bahaya', result.riskScore, scheme),
            const SizedBox(height: 16),
            _nseaeSection(scores, scheme),
            const SizedBox(height: 16),
            Text(result.explanation),
            const SizedBox(height: 16),
            _actionBanner(result.recommendedAction, scheme),
          ],
        ),
      ),
    );
  }

  Widget _scoreCard(String label, double value, ColorScheme scheme) {
    final percent = (value * 100).round();
    return Container(
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
    );
  }

  Widget _nseaeSection(dynamic scores, ColorScheme scheme) {
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
      padding: const EdgeInsets.all(14),
      decoration: BoxDecoration(
        color: scheme.surfaceContainerHighest,
        borderRadius: BorderRadius.circular(12),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Text(
            'Mengapa hasilnya seperti ini?',
            style: TextStyle(fontWeight: FontWeight.bold),
          ),
          const SizedBox(height: 8),
          if (visible.isEmpty)
            const Text('Tidak ditemukan tanda manipulasi yang kuat.')
          else
            ...visible.map(
              (entry) => Padding(
                padding: const EdgeInsets.only(bottom: 6),
                child: Row(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Icon(
                      Icons.check_circle_outline,
                      size: 18,
                      color: scheme.primary,
                    ),
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

  Widget _actionBanner(String action, ColorScheme scheme) {
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
                  'Saran Tindakan:',
                  style: TextStyle(
                    fontWeight: FontWeight.bold,
                    color: scheme.onPrimaryContainer,
                  ),
                ),
                const SizedBox(height: 4),
                Text(action,
                    style: TextStyle(color: scheme.onPrimaryContainer)),
              ],
            ),
          ),
        ],
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    final scheme = Theme.of(context).colorScheme;

    return Scaffold(
      appBar: AppBar(
        title: const Text('Riwayat'),
        actions: [
          if (_entries.isNotEmpty)
            IconButton(
              icon: const Icon(Icons.delete_sweep),
              onPressed: () async {
                final confirmed = await showDialog<bool>(
                  context: context,
                  builder: (ctx) => AlertDialog(
                    title: const Text('Hapus Semua Riwayat?'),
                    content: const Text(
                        'Semua riwayat analisis akan dihapus secara permanen.'),
                    actions: [
                      TextButton(
                          onPressed: () => Navigator.pop(ctx, false),
                          child: const Text('Batal')),
                      TextButton(
                          onPressed: () => Navigator.pop(ctx, true),
                          child: const Text('Ya, Hapus')),
                    ],
                  ),
                );
                if (confirmed == true) {
                  await HistoryService.clear();
                  setState(() => _entries = []);
                }
              },
            ),
        ],
      ),
      body: _isLoading
          ? const Center(child: CircularProgressIndicator())
          : _entries.isEmpty
              ? Center(
                  child: Column(
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      Icon(Icons.history,
                          size: 64,
                          color:
                              scheme.onSurfaceVariant.withValues(alpha: 0.4)),
                      const SizedBox(height: 12),
                      Text(
                        'Belum ada riwayat analisis',
                        style: TextStyle(color: scheme.onSurfaceVariant),
                      ),
                    ],
                  ),
                )
              : ListView.builder(
                  itemCount: _entries.length,
                  itemBuilder: (ctx, i) {
                    final entry = _entries[i];
                    final result = entry.result;
                    final msg = entry.message.length > 60
                        ? '${entry.message.substring(0, 60)}...'
                        : entry.message;

                    return Card(
                      margin: const EdgeInsets.symmetric(
                          horizontal: 12, vertical: 4),
                      child: ListTile(
                        leading: Icon(
                          entry.source == HistorySource.notification
                              ? Icons.notifications
                              : Icons.edit_note,
                        ),
                        title: Text(msg,
                            maxLines: 2, overflow: TextOverflow.ellipsis),
                        subtitle: Text(
                          '${result.kategoriNusaGuard} · ${_formatTimestamp(entry.timestamp)}',
                        ),
                        trailing: Container(
                          padding: const EdgeInsets.symmetric(
                              horizontal: 8, vertical: 4),
                          decoration: BoxDecoration(
                            color: _riskColor(result.riskLevel)
                                .withValues(alpha: 0.15),
                            borderRadius: BorderRadius.circular(8),
                          ),
                          child: Text(
                            result.riskLevel,
                            style: TextStyle(
                              fontSize: 12,
                              fontWeight: FontWeight.bold,
                              color: _riskColor(result.riskLevel),
                            ),
                          ),
                        ),
                        onTap: () => _showDetail(entry),
                      ),
                    );
                  },
                ),
    );
  }
}
