# NusaGuard Android

Flutter UI communicates with the native Kotlin `NotificationListenerService` through `id.nusaguard/notifications`. Only new notification body text from WhatsApp packages is forwarded; title/contact metadata and chat history are excluded.

Generate missing platform boilerplate once with Flutter installed (`flutter create --platforms android .`), preserving the checked-in `lib/main.dart`, manifest, and Kotlin files. Run with the shared backend:

```bash
flutter pub get
flutter run --dart-define=API_URL=https://your-api.example.com
```

For a live demo, grant notification access on the consent screen, send one controlled WhatsApp test message, and verify the high-priority NusaGuard warning. Production builds must use HTTPS and set `usesCleartextTraffic="false"`.
