import 'package:flutter_test/flutter_test.dart';
import 'package:nusaguard_android/main.dart';

void main() {
  testWidgets('App renders', (WidgetTester tester) async {
    await tester.pumpWidget(const NusaGuardApp());
    expect(find.text('NusaGuard'), findsOneWidget);
  });
}
