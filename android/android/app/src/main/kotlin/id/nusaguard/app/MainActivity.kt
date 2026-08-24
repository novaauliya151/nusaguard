package id.nusaguard.app

import android.app.NotificationChannel
import android.app.NotificationManager
import android.content.Intent
import android.provider.Settings
import androidx.core.app.NotificationCompat
import io.flutter.embedding.android.FlutterActivity
import io.flutter.embedding.engine.FlutterEngine
import io.flutter.plugin.common.MethodChannel

class MainActivity : FlutterActivity() {
    companion object { var bridge: MethodChannel? = null; const val CHANNEL = "id.nusaguard/notifications" }
    override fun configureFlutterEngine(engine: FlutterEngine) {
        super.configureFlutterEngine(engine)
        bridge = MethodChannel(engine.dartExecutor.binaryMessenger, CHANNEL)
        bridge?.setMethodCallHandler { call, result -> when(call.method) {
            "openNotificationAccess" -> { startActivity(Intent(Settings.ACTION_NOTIFICATION_LISTENER_SETTINGS)); result.success(null) }
            "showWarning" -> { showWarning(call.argument<String>("title") ?: "NusaGuard", call.argument<String>("body") ?: "Pesan mencurigakan"); result.success(null) }
            else -> result.notImplemented()
        }}
    }
    private fun showWarning(title:String, body:String) {
        val manager=getSystemService(NotificationManager::class.java)
        manager.createNotificationChannel(NotificationChannel("risk","Peringatan risiko",NotificationManager.IMPORTANCE_HIGH))
        manager.notify(151,NotificationCompat.Builder(this,"risk").setSmallIcon(android.R.drawable.ic_dialog_alert).setContentTitle(title).setContentText(body).setStyle(NotificationCompat.BigTextStyle().bigText(body)).setPriority(NotificationCompat.PRIORITY_HIGH).build())
    }
}
