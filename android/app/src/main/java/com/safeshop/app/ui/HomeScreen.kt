package com.safeshop.app.ui

import android.Manifest
import android.content.Context
import android.content.Intent
import android.net.Uri
import android.os.Build
import android.provider.Settings
import androidx.activity.compose.rememberLauncherForActivityResult
import androidx.activity.result.contract.ActivityResultContracts
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.Button
import androidx.compose.material3.Card
import androidx.compose.material3.CardDefaults
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.safeshop.app.data.BackendConfig
import com.safeshop.app.overlay.OverlayService

private enum class Screen { Home, Camera }

@Composable
fun AppRoot() {
    var screen by remember { mutableStateOf(Screen.Home) }
    when (screen) {
        Screen.Home -> HomeScreen(onOpenCamera = { screen = Screen.Camera })
        Screen.Camera -> CameraScreen(onClose = { screen = Screen.Home })
    }
}

private fun canDrawOverlays(context: Context): Boolean = Settings.canDrawOverlays(context)

@Composable
fun HomeScreen(onOpenCamera: () -> Unit) {
    val context = LocalContext.current
    var overlayGranted by remember { mutableStateOf(canDrawOverlays(context)) }
    var backendUrl by remember { mutableStateOf(BackendConfig.getBaseUrl(context)) }
    var backendSaved by remember { mutableStateOf(false) }

    val cameraPermissionLauncher = rememberLauncherForActivityResult(
        ActivityResultContracts.RequestPermission()
    ) { granted -> if (granted) onOpenCamera() }

    val notificationLauncher = rememberLauncherForActivityResult(
        ActivityResultContracts.RequestPermission()
    ) { }

    val overlaySettingsLauncher = rememberLauncherForActivityResult(
        ActivityResultContracts.StartActivityForResult()
    ) { overlayGranted = canDrawOverlays(context) }

    Column(
        modifier = Modifier
            .fillMaxSize()
            .background(MaterialTheme.colorScheme.background)
            .verticalScroll(rememberScrollState())
            .padding(20.dp)
    ) {
        Text(
            "SafeShop",
            color = Color.White,
            fontSize = 28.sp,
            fontWeight = FontWeight.Bold
        )
        Text(
            "Check how healthy a packaged food is - while you shop.",
            color = Color(0xCCFFFFFF),
            fontSize = 14.sp,
            modifier = Modifier.padding(top = 4.dp)
        )

        Spacer(Modifier.height(24.dp))

        // Camera mode
        Card(
            modifier = Modifier.fillMaxWidth(),
            shape = RoundedCornerShape(16.dp),
            colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.surface)
        ) {
            Column(Modifier.padding(16.dp)) {
                Text("Scan a label", color = Color.White, fontWeight = FontWeight.SemiBold, fontSize = 16.sp)
                Text(
                    "Point your camera at a product's ingredients / nutrition panel.",
                    color = Color(0xB3FFFFFF),
                    fontSize = 13.sp,
                    modifier = Modifier.padding(top = 4.dp, bottom = 12.dp)
                )
                Button(
                    onClick = { cameraPermissionLauncher.launch(Manifest.permission.CAMERA) },
                    modifier = Modifier.fillMaxWidth()
                ) { Text("Open camera scanner") }
            }
        }

        Spacer(Modifier.height(16.dp))

        // Overlay mode
        Card(
            modifier = Modifier.fillMaxWidth(),
            shape = RoundedCornerShape(16.dp),
            colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.surface)
        ) {
            Column(Modifier.padding(16.dp)) {
                Text("Overlay on shopping apps", color = Color.White, fontWeight = FontWeight.SemiBold, fontSize = 16.sp)
                Text(
                    "Shows a floating SafeShop bubble on top of any app. Open a product in your shopping app, tap the bubble, and it reads the screen and scores it. You keep ordering in that app. Screen access is asked once - after that, tap the bubble to scan as many products as you like; use the SafeShop notification's Stop when you're done.",
                    color = Color(0xB3FFFFFF),
                    fontSize = 13.sp,
                    modifier = Modifier.padding(top = 4.dp, bottom = 12.dp)
                )
                Text(
                    if (overlayGranted) "Overlay permission: granted" else "Overlay permission: needed",
                    color = if (overlayGranted) Color(0xFF22C55E) else Color(0xFFF59E0B),
                    fontSize = 12.sp,
                    modifier = Modifier.padding(bottom = 10.dp)
                )
                if (!overlayGranted) {
                    OutlinedButton(
                        onClick = {
                            overlaySettingsLauncher.launch(
                                Intent(
                                    Settings.ACTION_MANAGE_OVERLAY_PERMISSION,
                                    Uri.parse("package:" + context.packageName)
                                )
                            )
                        },
                        modifier = Modifier.fillMaxWidth()
                    ) { Text("Grant overlay permission") }
                } else {
                    Button(
                        onClick = {
                            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.TIRAMISU) {
                                notificationLauncher.launch(Manifest.permission.POST_NOTIFICATIONS)
                            }
                            OverlayService.start(context)
                        },
                        modifier = Modifier.fillMaxWidth()
                    ) { Text("Start SafeShop bubble") }
                }
            }
        }

        Spacer(Modifier.height(16.dp))

        // Backend connection
        Card(
            modifier = Modifier.fillMaxWidth(),
            shape = RoundedCornerShape(16.dp),
            colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.surface)
        ) {
            Column(Modifier.padding(16.dp)) {
                Text("Backend connection", color = Color.White, fontWeight = FontWeight.SemiBold, fontSize = 16.sp)
                Text(
                    "Over WiFi, put your computer's local IP here (e.g. http://192.168.1.5:8000). Same WiFi network, backend started with --host 0.0.0.0. Over USB you can instead keep 127.0.0.1 and run 'adb reverse tcp:8000 tcp:8000'.",
                    color = Color(0xB3FFFFFF),
                    fontSize = 13.sp,
                    modifier = Modifier.padding(top = 4.dp, bottom = 12.dp)
                )
                OutlinedTextField(
                    value = backendUrl,
                    onValueChange = { backendUrl = it; backendSaved = false },
                    singleLine = true,
                    label = { Text("Backend URL") },
                    modifier = Modifier.fillMaxWidth()
                )
                Spacer(Modifier.height(10.dp))
                Button(
                    onClick = {
                        BackendConfig.setBaseUrl(context, backendUrl)
                        backendUrl = BackendConfig.getBaseUrl(context)
                        backendSaved = true
                    },
                    modifier = Modifier.fillMaxWidth()
                ) { Text(if (backendSaved) "Saved" else "Save backend URL") }
            }
        }

        Spacer(Modifier.height(20.dp))
    }
}
