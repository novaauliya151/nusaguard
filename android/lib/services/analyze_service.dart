import 'dart:convert';
import 'package:http/http.dart' as http;
import '../models/analyze_result.dart';

const _apiUrl = String.fromEnvironment('API_URL', defaultValue: 'http://10.0.2.2:8000');

class AnalyzeService {
  Future<AnalyzeResult> analyzeMessage(String text, {String? source}) async {
    final r = await http.post(
      Uri.parse('$_apiUrl/api/analyze'),
      headers: {'Content-Type': 'application/json'},
      body: jsonEncode({'message': text, 'source': source}),
    );
    final data = jsonDecode(r.body) as Map<String, dynamic>;
    return AnalyzeResult.fromJson(data);
  }
}
