import 'dart:convert';
import 'package:http/http.dart' as http;
import '../models/analyze_result.dart';
import 'api_config.dart';

class AnalyzeService {
  AnalyzeService() {
    ensureProductionApiConfigured();
  }

  Future<AnalyzeResult> analyzeMessage(String text, {String? source}) async {
    final r = await http
        .post(
          Uri.parse('$apiUrl/api/analyze'),
          headers: {'Content-Type': 'application/json'},
          body: jsonEncode({'message': text, 'source': source}),
        )
        .timeout(const Duration(seconds: 60));
    if (r.statusCode != 200) {
      throw Exception('Analisis gagal (status ${r.statusCode})');
    }
    final data = jsonDecode(r.body) as Map<String, dynamic>;
    return AnalyzeResult.fromJson(data);
  }
}
