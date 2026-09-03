import 'analyze_result.dart';

enum HistorySource { manual, notification }

class HistoryEntry {
  final String id;
  final String message;
  final AnalyzeResult result;
  final HistorySource source;
  final DateTime timestamp;

  HistoryEntry({
    String? id,
    required this.message,
    required this.result,
    required this.source,
    DateTime? timestamp,
  })  : id = id ?? DateTime.now().millisecondsSinceEpoch.toString(),
        timestamp = timestamp ?? DateTime.now();

  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'message': message,
      'result': result.toJson(),
      'source': source.name,
      'timestamp': timestamp.toIso8601String(),
    };
  }

  factory HistoryEntry.fromJson(Map<String, dynamic> json) {
    return HistoryEntry(
      id: json['id'] as String,
      message: json['message'] as String,
      result: AnalyzeResult.fromJson(json['result'] as Map<String, dynamic>),
      source: HistorySource.values.firstWhere((e) => e.name == json['source']),
      timestamp: DateTime.parse(json['timestamp'] as String),
    );
  }
}
