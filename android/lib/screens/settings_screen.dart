import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import '../models/user.dart';
import '../services/auth_service.dart';
import '../services/notification_bridge_service.dart';
import '../utils/seed_dummy_history.dart';
import 'login_screen.dart';

class SettingsScreen extends StatefulWidget {
  const SettingsScreen({super.key});

  @override
  State<SettingsScreen> createState() => _SettingsScreenState();
}

class _SettingsScreenState extends State<SettingsScreen> {
  User? _currentUser;
  bool _isLoadingUser = true;

  @override
  void initState() {
    super.initState();
    _loadUser();
  }

  Future<void> _loadUser() async {
    final user = await AuthService().getCurrentUser();
    if (mounted) {
      setState(() {
        _currentUser = user;
        _isLoadingUser = false;
      });
    }
  }

  Future<void> _handleLogout() async {
    final confirmed = await showDialog<bool>(
      context: context,
      builder: (_) => AlertDialog(
        title: const Text('Keluar'),
        content: const Text('Yakin ingin keluar?'),
        actions: [
          TextButton(
            onPressed: () => Navigator.of(context).pop(false),
            child: const Text('Batal'),
          ),
          FilledButton(
            onPressed: () => Navigator.of(context).pop(true),
            child: const Text('Ya'),
          ),
        ],
      ),
    );

    if (confirmed == true) {
      await AuthService().logout();
      if (mounted) {
        Navigator.of(context).pushAndRemoveUntil(
          MaterialPageRoute(builder: (_) => const LoginScreen()),
          (route) => false,
        );
      }
    }
  }

  Future<void> _handleOpenNotificationSettings() async {
    ScaffoldMessenger.of(context).showSnackBar(
      const SnackBar(content: Text('Membuka pengaturan notifikasi...')),
    );
    try {
      await NotificationBridgeService.openNotificationSettings();
    } on PlatformException catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('Gagal membuka pengaturan: ${e.message}'),
            backgroundColor: Theme.of(context).colorScheme.error,
          ),
        );
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('Gagal membuka pengaturan: $e'),
            backgroundColor: Theme.of(context).colorScheme.error,
          ),
        );
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    final scheme = Theme.of(context).colorScheme;

    return Scaffold(
      appBar: AppBar(title: const Text('Pengaturan')),
      body: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          Card(
            child: Padding(
              padding: const EdgeInsets.all(18),
              child: _isLoadingUser
                  ? const Center(
                      child: Padding(
                        padding: EdgeInsets.all(12),
                        child: CircularProgressIndicator(),
                      ),
                    )
                  : _currentUser == null
                      ? const Center(child: Text('Gagal memuat profil.'))
                      : Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Row(
                              children: [
                                CircleAvatar(
                                  radius: 28,
                                  backgroundColor: scheme.primaryContainer,
                                  child: Text(
                                    _currentUser!.name.isNotEmpty
                                        ? _currentUser!.name[0].toUpperCase()
                                        : '?',
                                    style: TextStyle(
                                      fontSize: 24,
                                      fontWeight: FontWeight.bold,
                                      color: scheme.onPrimaryContainer,
                                    ),
                                  ),
                                ),
                                const SizedBox(width: 16),
                                Expanded(
                                  child: Column(
                                    crossAxisAlignment: CrossAxisAlignment.start,
                                    children: [
                                      Text(
                                        _currentUser!.name,
                                        style: const TextStyle(
                                          fontSize: 18,
                                          fontWeight: FontWeight.bold,
                                        ),
                                      ),
                                      const SizedBox(height: 2),
                                      Text(
                                        _currentUser!.email,
                                        style: TextStyle(
                                          fontSize: 13,
                                          color: scheme.onSurfaceVariant,
                                        ),
                                      ),
                                      const SizedBox(height: 2),
                                      Text(
                                        'Peran: ${_currentUser!.role}',
                                        style: TextStyle(
                                          fontSize: 12,
                                          color: scheme.onSurfaceVariant,
                                        ),
                                      ),
                                    ],
                                  ),
                                ),
                              ],
                            ),
                            const Divider(height: 32),
                            SizedBox(
                              width: double.infinity,
                              child: OutlinedButton.icon(
                                onPressed: _handleLogout,
                                icon: Icon(Icons.logout, color: scheme.error),
                                label: Text(
                                  'Keluar',
                                  style: TextStyle(color: scheme.error),
                                ),
                                style: OutlinedButton.styleFrom(
                                  side: BorderSide(color: scheme.error),
                                ),
                              ),
                            ),
                          ],
                        ),
            ),
          ),
          Card(
            child: Padding(
              padding: const EdgeInsets.all(18),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Row(
                    children: [
                      Icon(Icons.notifications_active_outlined, color: scheme.primary),
                      const SizedBox(width: 12),
                      const Expanded(
                        child: Text(
                          'Deteksi Otomatis WhatsApp',
                          style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold),
                        ),
                      ),
                    ],
                  ),
                  const SizedBox(height: 12),
                  const Text(
                    'Fitur ini memantau notifikasi WhatsApp masuk secara otomatis '
                    'dan memberi peringatan jika terdeteksi mencurigakan, '
                    'tanpa perlu membuka aplikasi.',
                  ),
                  const SizedBox(height: 16),
                  FilledButton.icon(
                    onPressed: _handleOpenNotificationSettings,
                    icon: const Icon(Icons.settings_outlined),
                    label: const Text('Aktifkan Izin Notifikasi'),
                  ),
                  const SizedBox(height: 8),
                  Text(
                    "Setelah menekan tombol ini, cari 'NusaGuard' di daftar aplikasi "
                    'pada halaman Settings yang terbuka, lalu aktifkan aksesnya.',
                    style: TextStyle(
                      fontSize: 12,
                      color: scheme.onSurfaceVariant,
                    ),
                  ),
                ],
              ),
            ),
          ),
          const Divider(height: 32),
          Center(
            child: Column(
              children: [
                Text(
                  'NusaGuard v0.1.0 (MVP)',
                  style: TextStyle(color: scheme.onSurfaceVariant),
                ),
                const SizedBox(height: 4),
                Text(
                  'Framework deteksi social engineering berbahasa Indonesia',
                  style: TextStyle(fontSize: 12, color: scheme.onSurfaceVariant),
                ),
              ],
            ),
          ),
          const SizedBox(height: 24),
          const Divider(height: 16),
          TextButton(
            onPressed: () async {
              final messenger = ScaffoldMessenger.of(context);
              await seedDummyHistory();
              if (mounted) {
                messenger.showSnackBar(
                  const SnackBar(content: Text('Data demo berhasil ditambahkan ke Riwayat')),
                );
              }
            },
            child: Text(
              'Isi Data Demo (Testing)',
              style: TextStyle(color: scheme.primary, fontWeight: FontWeight.w500),
            ),
          ),
        ],
      ),
    );
  }
}
