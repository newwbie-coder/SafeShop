package com.safeshop.app.overlay

import android.app.Activity
import android.media.projection.MediaProjectionManager
import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.result.contract.ActivityResultContracts

/** Transparent activity that asks the user for screen-capture consent, then hands the token to the service. */
class ProjectionRequestActivity : ComponentActivity() {

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)

        val manager = getSystemService(MEDIA_PROJECTION_SERVICE) as MediaProjectionManager

        val launcher = registerForActivityResult(
            ActivityResultContracts.StartActivityForResult()
        ) { result ->
            if (result.resultCode == Activity.RESULT_OK && result.data != null) {
                MediaProjectionHolder.resultCode = result.resultCode
                MediaProjectionHolder.data = result.data
                OverlayService.requestCapture(this)
            }
            finish()
        }

        launcher.launch(manager.createScreenCaptureIntent())
    }
}
