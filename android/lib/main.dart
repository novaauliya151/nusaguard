import 'package:flutter/material.dart';

import 'screens/auth_gate_screen.dart';
import 'services/notification_bridge_service.dart';

Future<void> main() async {
  WidgetsFlutterBinding.ensureInitialized();
  await NotificationBridgeService.initialize();
  runApp(const NusaGuardApp());
}

class NusaGuardApp extends StatelessWidget {
  const NusaGuardApp({super.key});

  @override
  Widget build(BuildContext context) {
    const darkGreen = Color(0xFF0D211C);
    const forestGreen = Color(0xFF173C32);
    const lime = Color(0xFFB9EF68);
    const cream = Color(0xFFF4F1E8);

    return MaterialApp(
      title: 'NusaGuard',
      debugShowCheckedModeBanner: false,
      theme: ThemeData(
        useMaterial3: true,
        scaffoldBackgroundColor: cream,
        colorScheme: ColorScheme.fromSeed(
          seedColor: forestGreen,
          brightness: Brightness.light,
          primary: forestGreen,
          secondary: lime,
          surface: cream,
        ),
        appBarTheme: const AppBarTheme(
          centerTitle: false,
          backgroundColor: cream,
          foregroundColor: darkGreen,
          elevation: 0,
        ),
        inputDecorationTheme: InputDecorationTheme(
          filled: true,
          fillColor: Colors.white,
          border: OutlineInputBorder(
            borderRadius: BorderRadius.circular(12),
          ),
        ),
      ),
      home: const AuthGateScreen(),
    );
  }
}
