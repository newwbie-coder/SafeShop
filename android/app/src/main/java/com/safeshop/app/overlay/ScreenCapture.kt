package com.safeshop.app.overlay

import android.graphics.Bitmap
import android.graphics.PixelFormat
import android.hardware.display.DisplayManager
import android.hardware.display.VirtualDisplay
import android.media.ImageReader
import android.media.projection.MediaProjection
import android.os.Handler
import android.os.Looper
import android.util.DisplayMetrics

/** Captures a single frame of the screen via MediaProjection and returns it as a Bitmap. */
class ScreenCapture(
    private val projection: MediaProjection,
    private val metrics: DisplayMetrics
) {
    private val handler = Handler(Looper.getMainLooper())

    fun captureOnce(onBitmap: (Bitmap?) -> Unit) {
        val width = metrics.widthPixels
        val height = metrics.heightPixels
        val density = metrics.densityDpi

        // Android 14 requires a registered callback before creating a virtual display.
        projection.registerCallback(object : MediaProjection.Callback() {}, handler)

        val reader = ImageReader.newInstance(width, height, PixelFormat.RGBA_8888, 2)

        var virtualDisplay: VirtualDisplay? = null
        var delivered = false

        reader.setOnImageAvailableListener({ r ->
            if (delivered) return@setOnImageAvailableListener
            val image = r.acquireLatestImage() ?: return@setOnImageAvailableListener
            delivered = true

            val bitmap = try {
                val plane = image.planes[0]
                val buffer = plane.buffer
                val pixelStride = plane.pixelStride
                val rowStride = plane.rowStride
                val rowPadding = rowStride - pixelStride * width

                val full = Bitmap.createBitmap(
                    width + rowPadding / pixelStride,
                    height,
                    Bitmap.Config.ARGB_8888
                )
                full.copyPixelsFromBuffer(buffer)
                Bitmap.createBitmap(full, 0, 0, width, height)
            } catch (e: Exception) {
                null
            } finally {
                image.close()
            }

            r.setOnImageAvailableListener(null, null)
            virtualDisplay?.release()
            r.close()
            onBitmap(bitmap)
        }, handler)

        virtualDisplay = projection.createVirtualDisplay(
            "safeshop-capture",
            width,
            height,
            density,
            DisplayManager.VIRTUAL_DISPLAY_FLAG_AUTO_MIRROR,
            reader.surface,
            null,
            handler
        )
    }
}
