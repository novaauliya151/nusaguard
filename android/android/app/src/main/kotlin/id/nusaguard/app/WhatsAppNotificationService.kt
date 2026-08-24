package id.nusaguard.app

import android.service.notification.NotificationListenerService
import android.service.notification.StatusBarNotification

class WhatsAppNotificationService : NotificationListenerService() {
    override fun onNotificationPosted(sbn: StatusBarNotification) {
        if (sbn.packageName != "com.whatsapp" && sbn.packageName != "com.whatsapp.w4b") return
        val extras=sbn.notification.extras
        val text=extras.getCharSequence("android.text")?.toString()?.trim().orEmpty()
        if (text.isNotEmpty()) MainActivity.bridge?.invokeMethod("notificationText",text)
    }
}
