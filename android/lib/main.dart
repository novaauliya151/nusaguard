import 'package:flutter/material.dart';
import 'screens/auth_gate_screen.dart';
import 'services/notification_bridge_service.dart';

void main() {
  WidgetsFlutterBinding.ensureInitialized();
  NotificationBridgeService.initialize();
  NotificationBridgeService.requestBatteryOptimizationExemption();
  runApp(const NusaGuardApp());
}

class NusaGuardApp extends StatelessWidget {
  const NusaGuardApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      debugShowCheckedModeBanner: false,
      theme: ThemeData(
        colorScheme: ColorScheme.fromSeed(seedColor: const Color(0xff1d4b3d)),
      ),
      home: const AuthGateScreen(),
    );
  }
}
