package com.safeshop.app.ui

import android.util.Log
import androidx.camera.core.CameraSelector
import androidx.camera.core.ExperimentalGetImage
import androidx.camera.core.ImageAnalysis
import androidx.camera.core.ImageProxy
import androidx.camera.core.Preview
import androidx.camera.lifecycle.ProcessCameraProvider
import androidx.camera.view.PreviewView
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.Button
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.rememberCoroutineScope
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.platform.LocalContext
import androidx.lifecycle.compose.LocalLifecycleOwner
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.compose.ui.viewinterop.AndroidView
import androidx.core.content.ContextCompat
import com.google.mlkit.vision.common.InputImage
import com.google.mlkit.vision.text.TextRecognition
import com.google.mlkit.vision.text.latin.TextRecognizerOptions
import com.safeshop.app.data.AnalyzeResponse
import com.safeshop.app.data.AnalyzeResult
import com.safeshop.app.data.Analyzer
import kotlinx.coroutines.launch
import java.util.concurrent.Executors

@Composable
fun CameraScreen(onClose: () -> Unit) {
    val context = LocalContext.current
    val lifecycleOwner = LocalLifecycleOwner.current
    val scope = rememberCoroutineScope()
    val analysisExecutor = remember { Executors.newSingleThreadExecutor() }

    var detectedText by remember { mutableStateOf("") }
    var analyzing by remember { mutableStateOf(false) }
    var result by remember { mutableStateOf<AnalyzeResponse?>(null) }
    var error by remember { mutableStateOf<String?>(null) }

    Box(modifier = Modifier.fillMaxSize().background(Color.Black)) {
        AndroidView(
            modifier = Modifier.fillMaxSize(),
            factory = { ctx ->
                val previewView = PreviewView(ctx)
                val providerFuture = ProcessCameraProvider.getInstance(ctx)
                providerFuture.addListener({
                    val provider = providerFuture.get()
                    val preview = Preview.Builder().build().also {
                        it.setSurfaceProvider(previewView.surfaceProvider)
                    }
                    val analysis = ImageAnalysis.Builder()
                        .setBackpressureStrategy(ImageAnalysis.STRATEGY_KEEP_ONLY_LATEST)
                        .build()
                    analysis.setAnalyzer(analysisExecutor, OcrFrameAnalyzer { text ->
                        if (text.isNotBlank()) detectedText = text
                    })
                    try {
                        provider.unbindAll()
                        provider.bindToLifecycle(
                            lifecycleOwner,
                            CameraSelector.DEFAULT_BACK_CAMERA,
                            preview,
                            analysis
                        )
                    } catch (e: Exception) {
                        Log.e("CameraScreen", "bind failed", e)
                    }
                }, ContextCompat.getMainExecutor(ctx))
                previewView
            }
        )

        // Bottom controls
        Column(
            modifier = Modifier
                .align(Alignment.BottomCenter)
                .fillMaxWidth()
                .background(Color(0xAA000000))
                .padding(16.dp)
        ) {
            Text(
                if (detectedText.isBlank()) "Point at the ingredients / nutrition panel..."
                else "Detected ${detectedText.length} characters of text",
                color = Color.White,
                fontSize = 13.sp
            )
            Spacer(Modifier.height(10.dp))
            Row(horizontalArrangement = Arrangement.spacedBy(12.dp)) {
                OutlinedButton(onClick = onClose) { Text("Back") }
                Button(
                    onClick = {
                        error = null
                        analyzing = true
                        val snapshot = detectedText
                        scope.launch {
                            when (val r = Analyzer.analyze("Camera scan", snapshot)) {
                                is AnalyzeResult.Success -> result = r.response
                                is AnalyzeResult.Error -> error = r.message
                            }
                            analyzing = false
                        }
                    },
                    enabled = !analyzing && detectedText.isNotBlank(),
                    modifier = Modifier.weight(1f)
                ) { Text(if (analyzing) "Analyzing..." else "Analyze this label") }
            }
            error?.let {
                Spacer(Modifier.height(8.dp))
                Text(it, color = Color(0xFFEF4444), fontSize = 12.sp)
            }
        }

        if (analyzing) {
            CircularProgressIndicator(
                modifier = Modifier.align(Alignment.Center),
                color = Color(0xFF22C55E)
            )
        }

        // Result overlay
        result?.let { res ->
            Box(
                modifier = Modifier
                    .fillMaxSize()
                    .background(Color(0xCC000000))
                    .padding(16.dp)
            ) {
                Column(
                    modifier = Modifier
                        .align(Alignment.Center)
                        .fillMaxWidth()
                        .verticalScroll(rememberScrollState())
                ) {
                    ScoreCard(res)
                    Spacer(Modifier.height(12.dp))
                    Button(
                        onClick = { result = null },
                        modifier = Modifier.fillMaxWidth()
                    ) { Text("Scan again") }
                }
            }
        }
    }
}

@ExperimentalGetImage
private class OcrFrameAnalyzer(val onText: (String) -> Unit) : ImageAnalysis.Analyzer {
    private val recognizer = TextRecognition.getClient(TextRecognizerOptions.DEFAULT_OPTIONS)

    override fun analyze(imageProxy: ImageProxy) {
        val media = imageProxy.image
        if (media == null) {
            imageProxy.close()
            return
        }
        val image = InputImage.fromMediaImage(media, imageProxy.imageInfo.rotationDegrees)
        recognizer.process(image)
            .addOnSuccessListener { onText(it.text) }
            .addOnCompleteListener { imageProxy.close() }
    }
}
