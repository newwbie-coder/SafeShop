package com.safeshop.app

import android.app.Application
import android.content.Intent
import android.os.Process
import java.io.File
import kotlin.system.exitProcess

/**
 * Catches any uncaught exception, saves the stack trace to a shareable file, and
 * shows it on screen (in a separate :crash process) so a crash can be diagnosed on
 * a physical device without adb. Diagnostic aid - safe to remove once stable.
 */
class SafeShopApp : Application() {
    override fun onCreate() {
        super.onCreate()
        val previous = Thread.getDefaultUncaughtExceptionHandler()
        Thread.setDefaultUncaughtExceptionHandler { thread, throwable ->
            try {
                val trace = android.util.Log.getStackTraceString(throwable)
                val text = "SafeShop crash\nThread: ${thread.name}\n\n$trace"
                try {
                    getExternalFilesDir(null)?.let { File(it, "last_crash.txt").writeText(text) }
                } catch (_: Throwable) {
                }
                val i = Intent(this, CrashActivity::class.java)
                    .addFlags(Intent.FLAG_ACTIVITY_NEW_TASK or Intent.FLAG_ACTIVITY_CLEAR_TASK)
                    .putExtra(CrashActivity.EXTRA_TRACE, text)
                startActivity(i)
            } catch (t: Throwable) {
                previous?.uncaughtException(thread, throwable)
            }
            Process.killProcess(Process.myPid())
            exitProcess(10)
        }
    }
}
