package id.nusaguard.app

import android.content.Context
import android.os.Build
import android.os.Bundle
import android.service.notification.NotificationListenerService
import android.service.notification.StatusBarNotification
import android.util.Log

class WhatsAppNotificationService : NotificationListenerService() {
    private val TAG = "NusaGuardWhatsApp"

    override fun onCreate() {
        super.onCreate()
        Log.d(TAG, "WhatsAppNotificationService created")
    }

    override fun onNotificationPosted(sbn: StatusBarNotification) {
        val pkg = sbn.packageName
        if (pkg != "com.whatsapp" && pkg != "com.whatsapp.w4b") return

        val extras = sbn.notification.extras
        val text = extractNotificationText(extras)
        val title = extras.getString(android.app.Notification.EXTRA_TITLE)?.trim() ?: ""
        val bigText = extras.getCharSequence(android.app.Notification.EXTRA_BIG_TEXT)?.toString()?.trim() ?: ""

        val combinedText = buildCombinedText(title, text, bigText)
        val sender = extractSender(title, bigText)

        if (combinedText.isNotEmpty() && combinedText.length >= 10) {
            Log.d(TAG, "WA Notification - Sender: $sender, Text: $combinedText")
            val payload = "$sender|$combinedText"
            MainActivity.bridge?.invokeMethod("notificationText", payload)
        } else {
            Log.d(TAG, "WA Notification ignored (too short or empty): '$combinedText'")
        }
    }

    override fun onNotificationRemoved(sbn: StatusBarNotification) {
        val pkg = sbn.packageName
        if (pkg == "com.whatsapp" || pkg == "com.whatsapp.w4b") {
            Log.d(TAG, "WA Notification removed: ${sbn.tag}")
        }
    }

    private fun extractNotificationText(extras: Bundle): String {
        val text = extras.getCharSequence("android.text")?.toString()?.trim() ?: ""
        val textLines = extras.getCharSequenceArray("android.textLines")
        if (text.isNotEmpty()) return text
        if (textLines != null) {
            return textLines.joinToString(" ") { it?.toString()?.trim() ?: "" }
        }
        return ""
    }

    private fun extractSender(title: String, bigText: String): String {
        if (title.isNotEmpty()) return title
        val colonIdx = bigText.indexOf(':')
        if (colonIdx > 0 && colonIdx < 50) {
            return bigText.substring(0, colonIdx).trim()
        }
        return "Unknown"
    }

    private fun buildCombinedText(title: String, text: String, bigText: String): String {
        val parts = mutableListOf<String>()
        if (bigText.isNotEmpty()) parts.add(bigText)
        else if (text.isNotEmpty()) parts.add(text)
        if (title.isNotEmpty() && !bigText.contains(title, ignoreCase = true)) {
            parts.add(0, title)
        }
        return parts.joinToString(" ")
    }
}