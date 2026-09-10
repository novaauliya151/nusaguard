import 'dart:convert';
import 'package:flutter/foundation.dart';
import 'package:shared_preferences/shared_preferences.dart';
import '../models/history_entry.dart';
import 'auth_service.dart';

class HistoryService {
  static const String _storageKeyPrefix = 'nusaguard_history';
  static const int _maxEntries = 100;
  static final ValueNotifier<int> changes = ValueNotifier<int>(0);

  static Future<String> _storageKey() async {
    final user = await AuthService().getCurrentUser();
    return '${_storageKeyPrefix}_${user?.id ?? 'guest'}';
  }

  static Future<List<HistoryEntry>> getAll() async {
    final prefs = await SharedPreferences.getInstance();
    final raw = prefs.getStringList(await _storageKey()) ?? [];
    final entries = <HistoryEntry>[];
    for (final s in raw) {
      try {
        entries
            .add(HistoryEntry.fromJson(jsonDecode(s) as Map<String, dynamic>));
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
      await _storageKey(),
      existing.map((e) => jsonEncode(e.toJson())).toList(),
    );
    changes.value++;
  }

  static Future<void> clear() async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.remove(await _storageKey());
    changes.value++;
  }

  static Future<void> deleteEntry(String id) async {
    final existing = await getAll();
    existing.removeWhere((e) => e.id == id);
    final prefs = await SharedPreferences.getInstance();
    await prefs.setStringList(
      await _storageKey(),
      existing.map((e) => jsonEncode(e.toJson())).toList(),
    );
    changes.value++;
  }
}
