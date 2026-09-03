package id.nusaguard.app

import android.app.NotificationChannel
import android.app.NotificationManager
import android.app.PendingIntent
import android.content.Context
import android.content.Intent
import android.net.Uri
import android.os.Build
import android.os.PowerManager
import android.provider.Settings
import androidx.core.app.NotificationCompat
import io.flutter.embedding.android.FlutterActivity
import io.flutter.embedding.engine.FlutterEngine
import io.flutter.plugin.common.MethodChannel

class MainActivity : FlutterActivity() {
    companion object {
        var bridge: MethodChannel? = null
        const val CHANNEL = "id.nusaguard/notifications"
        const val NOTIFICATION_CHANNEL_ID = "risk_warnings"
    }

    override fun configureFlutterEngine(engine: FlutterEngine) {
        super.configureFlutterEngine(engine)
        bridge = MethodChannel(engine.dartExecutor.binaryMessenger, CHANNEL)
        bridge?.setMethodCallHandler { call, result ->
            when (call.method) {
                "openNotificationAccess" -> {
                    startActivity(Intent(Settings.ACTION_NOTIFICATION_LISTENER_SETTINGS))
                    result.success(null)
                }
                "showWarning" -> {
                    val id = call.argument<Int>("id") ?: 151
                    val title = call.argument<String>("title") ?: "NusaGuard"
                    val body = call.argument<String>("body") ?: "Pesan mencurigakan terdeteksi"
                    val riskLevel = call.argument<String>("riskLevel") ?: "MEDIUM"
                    showWarning(id, title, body, riskLevel)
                    result.success(null)
                }
                "startListenerService" -> {
                    startListenerService()
                    result.success(null)
                }
                "requestBatteryOptimizationExemption" -> {
                    requestBatteryOptimizationExemption()
                    result.success(null)
                }
                "isBatteryOptimizationExempt" -> {
                    result.success(isBatteryOptimizationExempt())
                }
                else -> result.notImplemented()
            }
        }
    }

    private fun startListenerService() {
        val serviceIntent = Intent(this, NotificationListenerForegroundService::class.java)
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            startForegroundService(serviceIntent)
        } else {
            startService(serviceIntent)
        }
    }

    private fun requestBatteryOptimizationExemption() {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.M) {
            val pm = getSystemService(PowerManager::class.java)
            val packageName = packageName
            if (!pm.isIgnoringBatteryOptimizations(packageName)) {
                val intent = Intent(Settings.ACTION_REQUEST_IGNORE_BATTERY_OPTIMIZATIONS)
                intent.data = Uri.parse("package:$packageName")
                startActivity(intent)
            }
        }
    }

    private fun isBatteryOptimizationExempt(): Boolean {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.M) {
            val pm = getSystemService(PowerManager::class.java)
            return pm.isIgnoringBatteryOptimizations(packageName)
        }
        return true
    }

    private fun showWarning(id: Int, title: String, body: String, riskLevel: String) {
        val manager = getSystemService(NotificationManager::class.java)
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            val importance = if (riskLevel == "HIGH") NotificationManager.IMPORTANCE_HIGH else NotificationManager.IMPORTANCE_DEFAULT
            val channel = NotificationChannel(
                NOTIFICATION_CHANNEL_ID,
                "Peringatan Risiko NusaGuard",
                importance
            ).apply {
                description = "Notifikasi peringatan penipuan dari NusaGuard"
                enableVibration(true)
                setShowBadge(true)
            }
            manager.createNotificationChannel(channel)
        }

        val intent = Intent(this, MainActivity::class.java).apply {
            action = "OPEN_WARNING_DETAIL"
            putExtra("warning_title", title)
            putExtra("warning_body", body)
            putExtra("warning_risk_level", riskLevel)
            flags = Intent.FLAG_ACTIVITY_NEW_TASK or Intent.FLAG_ACTIVITY_CLEAR_TOP
        }
        val pendingIntent = PendingIntent.getActivity(
            this,
            id,
            intent,
            PendingIntent.FLAG_UPDATE_CURRENT or PendingIntent.FLAG_IMMUTABLE
        )

        val priority = if (riskLevel == "HIGH") NotificationCompat.PRIORITY_HIGH else NotificationCompat.PRIORITY_DEFAULT

        val builder = NotificationCompat.Builder(this, NOTIFICATION_CHANNEL_ID)
            .setSmallIcon(android.R.drawable.ic_dialog_alert)
            .setContentTitle(title)
            .setContentText(body)
            .setStyle(NotificationCompat.BigTextStyle().bigText(body))
            .setPriority(priority)
            .setContentIntent(pendingIntent)
            .setAutoCancel(true)
            .setCategory(NotificationCompat.CATEGORY_ALARM)

        manager.notify(id, builder.build())
    }
}