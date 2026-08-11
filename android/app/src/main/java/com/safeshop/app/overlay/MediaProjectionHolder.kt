package com.safeshop.app.overlay

import android.content.Intent

/** Holds the one-time MediaProjection consent token between the request activity and the service. */
object MediaProjectionHolder {
    var resultCode: Int = 0
    var data: Intent? = null

    fun hasPermission(): Boolean = data != null

    fun clear() {
        resultCode = 0
        data = null
    }
}
