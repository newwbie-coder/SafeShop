package com.safeshop.app.data

import android.content.Context
import com.safeshop.app.BuildConfig

/**
 * Backend base URL, editable at runtime (persisted in SharedPreferences) so the app can point
 * at a laptop's LAN IP over WiFi, an adb-reversed localhost, or a hosted URL later - without a rebuild.
 */
object BackendConfig {
    private const val PREFS = "safeshop_prefs"
    private const val KEY_BASE_URL = "base_url"

    @Volatile
    private var cached: String? = null

    fun getBaseUrl(context: Context): String {
        cached?.let { return it }
        val prefs = context.getSharedPreferences(PREFS, Context.MODE_PRIVATE)
        val value = prefs.getString(KEY_BASE_URL, BuildConfig.BASE_URL) ?: BuildConfig.BASE_URL
        cached = value
        return value
    }

    fun setBaseUrl(context: Context, url: String) {
        var normalized = url.trim()
        if (normalized.isEmpty()) normalized = BuildConfig.BASE_URL
        if (!normalized.startsWith("http://") && !normalized.startsWith("https://")) {
            normalized = "http://$normalized"
        }
        if (!normalized.endsWith("/")) normalized = "$normalized/"
        context.getSharedPreferences(PREFS, Context.MODE_PRIVATE)
            .edit()
            .putString(KEY_BASE_URL, normalized)
            .apply()
        cached = normalized
    }
}
