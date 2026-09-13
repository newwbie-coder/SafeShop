package com.safeshop.app.ocr

import android.graphics.Bitmap
import androidx.camera.core.ExperimentalGetImage
import androidx.camera.core.ImageProxy
import com.google.mlkit.vision.common.InputImage
import com.google.mlkit.vision.text.TextRecognition
import com.google.mlkit.vision.text.latin.TextRecognizerOptions
import kotlinx.coroutines.suspendCancellableCoroutine
import kotlin.coroutines.resume
import kotlin.coroutines.resumeWithException

/** On-device OCR (Google ML Kit, offline). Shared by camera and overlay capture. */
object TextRecognizerHelper {

    private val recognizer = TextRecognition.getClient(TextRecognizerOptions.DEFAULT_OPTIONS)

    suspend fun recognizeBitmap(bitmap: Bitmap): String =
        suspendCancellableCoroutine { cont ->
            val image = InputImage.fromBitmap(bitmap, 0)
            recognizer.process(image)
                .addOnSuccessListener { result -> cont.resume(result.text) }
                .addOnFailureListener { e -> cont.resumeWithException(e) }
        }

    /** Caller is responsible for closing [proxy] after this returns. */
    @ExperimentalGetImage
    suspend fun recognizeImageProxy(proxy: ImageProxy): String =
        suspendCancellableCoroutine { cont ->
            val media = proxy.image
            if (media == null) {
                cont.resume("")
                return@suspendCancellableCoroutine
            }
            val image = InputImage.fromMediaImage(media, proxy.imageInfo.rotationDegrees)
            recognizer.process(image)
                .addOnSuccessListener { result -> cont.resume(result.text) }
                .addOnFailureListener { e -> cont.resumeWithException(e) }
        }
}
