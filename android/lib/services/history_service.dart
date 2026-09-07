import 'dart:convert';
import 'package:shared_preferences/shared_preferences.dart';
import '../models/history_entry.dart';

class HistoryService {
  static const String _storageKey = 'nusaguard_history';
  static const int _maxEntries = 100;

  static Future<List<HistoryEntry>> getAll() async {
    final prefs = await SharedPreferences.getInstance();
    final raw = prefs.getStringList(_storageKey) ?? [];
    final entries = <HistoryEntry>[];
    for (final s in raw) {
      try {
        entries.add(HistoryEntry.fromJson(jsonDecode(s) as Map<String, dynamic>));
      } catch (_) {}
    }
    entries.sort((a, b) => b.timestamp.compareTo(a.timestamp));
    return entries;
  }

  static Future<void> add(HistoryEntry entry) async {
    final existing = await getAll();
    existing.insert(0, entry);
    if (existing.length > _maxEntries) {
      existing.removeRange(_maxEntries, existing.length);
    }
    final prefs = await SharedPreferences.getInstance();
    await prefs.setStringList(
      _storageKey,
      existing.map((e) => jsonEncode(e.toJson())).toList(),
    );
  }

  static Future<void> clear() async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.remove(_storageKey);
  }

  static Future<void> deleteEntry(String id) async {
    final existing = await getAll();
    existing.removeWhere((e) => e.id == id);
    final prefs = await SharedPreferences.getInstance();
    await prefs.setStringList(
      _storageKey,
      existing.map((e) => jsonEncode(e.toJson())).toList(),
    );
  }
}
