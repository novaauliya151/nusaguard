const String apiUrl = String.fromEnvironment(
  'API_URL',
  defaultValue:
      'https://transmitted-rebound-granted-administered.trycloudflare.com',
);

void ensureProductionApiConfigured() {
  const isRelease = bool.fromEnvironment('dart.vm.product');
  if (isRelease && !apiUrl.startsWith('https://')) {
    throw StateError(
      'Build release wajib memakai --dart-define=API_URL=https://alamat-backend',
    );
  }
}
