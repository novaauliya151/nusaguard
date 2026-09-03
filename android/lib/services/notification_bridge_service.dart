// NotificationBridgeService
//
// Panggil NotificationBridgeService.initialize() sekali saja di awal
// lifecycle app (misalnya di main.dart setelah runApp).
//
// Service ini TIDAK mengecek apakah user sudah memberi izin notification
// access. Itu tanggung jawab UI terpisah untuk mengarahkan user membuka
// settings dan approve secara manual lewat openNotificationSettings().

import 'dart:developer' as developer;
import 'package:flutter/services.dart';
import '../services/analyze_service.dart';
import '../services/history_service.dart';
import '../models/history_entry.dart';

class NotificationBridgeService {
  static const MethodChannel _channel =
      MethodChannel('id.nusaguard/notifications');

  static final AnalyzeService _analyzeService = AnalyzeService();
  static int _notificationCounter = 0;
  static bool _isInitialized = false;

  static Future<void> initialize() async {
    if (_isInitialized) return;
    developer.log('[NotificationBridge] Initializing...', name: 'NusaGuard');
    _channel.setMethodCallHandler((call) async {
      if (call.method == 'notificationText') {
        final payload = call.arguments as String;
        await _handleNotificationText(payload);
      }
      return null;
    });
    await startListenerService();
    _isInitialized = true;
    developer.log('[NotificationBridge] Initialized successfully', name: 'NusaGuard');
  }

  static Future<void> startListenerService() async {
    try {
      developer.log('[NotificationBridge] Starting foreground listener service...', name: 'NusaGuard');
      await _channel.invokeMethod('startListenerService');
      developer.log('[NotificationBridge] Foreground listener service started', name: 'NusaGuard');
    } catch (e) {
      developer.log('[NotificationBridge] Failed to start listener service: $e', name: 'NusaGuard');
    }
  }

  static Future<void> requestBatteryOptimizationExemption() async {
    try {
      developer.log('[NotificationBridge] Requesting battery optimization exemption...', name: 'NusaGuard');
      await _channel.invokeMethod('requestBatteryOptimizationExemption');
    } catch (e) {
      developer.log('[NotificationBridge] Failed to request battery exemption: $e', name: 'NusaGuard');
    }
  }

  static Future<bool> isBatteryOptimizationExempt() async {
    try {
      final result = await _channel.invokeMethod<bool>('isBatteryOptimizationExempt');
      return result ?? false;
    } catch (e) {
      developer.log('[NotificationBridge] Failed to check battery exemption: $e', name: 'NusaGuard');
      return false;
    }
  }

  static Future<void> _handleNotificationText(String payload) async {
    developer.log('[NotificationBridge] Received notification payload: $payload', name: 'NusaGuard');

    final parts = payload.split('|');
    if (parts.length < 2) {
      developer.log('[NotificationBridge] Invalid payload format (missing sender|text)', name: 'NusaGuard');
      return;
    }

    final sender = parts[0].trim();
    final text = parts.sublist(1).join('|').trim();

    developer.log('[NotificationBridge] Parsed - Sender: "$sender", Text length: ${text.length}', name: 'NusaGuard');

    if (text.isEmpty || text.length < 10) {
      developer.log('[NotificationBridge] Text too short, skipping analysis', name: 'NusaGuard');
      return;
    }

    try {
      developer.log('[NotificationBridge] Sending to backend /api/analyze...', name: 'NusaGuard');
      final result = await _analyzeService.analyzeMessage(
        text,
        source: 'android_notification',
      );

      developer.log(
        '[NotificationBridge] Analysis result: riskLevel=${result.riskLevel}, '
        'category=${result.kategoriNusaGuard}, riskScore=${result.riskScore}, '
        'confidence=${result.confidence}',
        name: 'NusaGuard',
      );

      await HistoryService.add(HistoryEntry(
        message: text,
        result: result,
        source: HistorySource.notification,
      ));
      developer.log('[NotificationBridge] Saved to history', name: 'NusaGuard');

      if (result.riskLevel == 'HIGH' || result.riskLevel == 'MEDIUM') {
        final title = result.riskLevel == 'HIGH'
            ? '⚠️ Risiko Tinggi Terdeteksi!'
            : 'Perhatian: Pesan Mencurigakan';
        final body = 'Dari: $sender\n${result.explanation}';

        developer.log('[NotificationBridge] Showing warning notification: $title', name: 'NusaGuard');
        await _showWarningNotification(title, body, result);
      } else {
        developer.log('[NotificationBridge] Risk level LOW - saved to history only, no notification', name: 'NusaGuard');
      }
    } catch (e, stackTrace) {
      developer.log(
        '[NotificationBridge] Analysis failed: $e',
        name: 'NusaGuard',
        error: e,
        stackTrace: stackTrace,
      );
    }
  }

  static Future<void> _showWarningNotification(
    String title,
    String body,
    dynamic result,
  ) async {
    _notificationCounter++;
    final notificationId = _notificationCounter;

    try {
      await _channel.invokeMethod('showWarning', {
        'id': notificationId,
        'title': title,
        'body': body,
        'riskLevel': result.riskLevel,
        'sender': result.kategoriNusaGuard,
      });
      developer.log('[NotificationBridge] Warning notification sent (id=$notificationId)', name: 'NusaGuard');
    } catch (e) {
      developer.log('[NotificationBridge] Failed to show warning: $e', name: 'NusaGuard');
    }
  }

  static Future<void> openNotificationSettings() async {
    developer.log('[NotificationBridge] Opening notification access settings', name: 'NusaGuard');
    await _channel.invokeMethod('openNotificationAccess');
  }
}