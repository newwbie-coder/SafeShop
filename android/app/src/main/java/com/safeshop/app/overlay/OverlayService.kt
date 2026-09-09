package com.safeshop.app.overlay

import android.app.Notification
import android.app.NotificationChannel
import android.app.NotificationManager
import android.app.PendingIntent
import android.app.Service
import android.content.Context
import android.content.Intent
import android.content.pm.ServiceInfo
import android.graphics.Color
import android.graphics.drawable.GradientDrawable
import android.media.projection.MediaProjection
import android.media.projection.MediaProjectionManager
import android.os.Build
import android.os.Handler
import android.os.IBinder
import android.os.Looper
import android.util.TypedValue
import android.view.Gravity
import android.view.MotionEvent
import android.view.View
import android.view.WindowManager
import android.widget.FrameLayout
import android.widget.TextView
import android.widget.Toast
import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.Button
import androidx.compose.material3.Text
import androidx.compose.runtime.mutableStateOf
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color as ComposeColor
import androidx.compose.ui.platform.ComposeView
import androidx.compose.ui.unit.dp
import com.safeshop.app.data.AnalyzeResponse
import com.safeshop.app.data.AnalyzeResult
import com.safeshop.app.data.Analyzer
import com.safeshop.app.ocr.TextRecognizerHelper
import com.safeshop.app.ui.ScoreCard
import com.safeshop.app.ui.theme.SafeShopTheme
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.SupervisorJob
import kotlinx.coroutines.cancel
import kotlinx.coroutines.delay
import kotlinx.coroutines.launch

class OverlayService : Service() {

    private lateinit var windowManager: WindowManager
    private var bubbleView: View? = null
    private var cardView: ComposeView? = null
    private var cardOwner: WindowLifecycleOwner? = null
    private val scope = CoroutineScope(Dispatchers.Main + SupervisorJob())

    // Kept alive for the whole session so the user only grants screen capture once
    // and can then scan repeatedly. Null until consent is granted, or after Stop /
    // the system revokes the projection.
    private var projection: MediaProjection? = null
    private var isForeground = false
    private val handler = Handler(Looper.getMainLooper())

    override fun onBind(intent: Intent?): IBinder? = null

    override fun onCreate() {
        super.onCreate()
        windowManager = getSystemService(WINDOW_SERVICE) as WindowManager
        createNotificationChannel()
    }

    override fun onStartCommand(intent: Intent?, flags: Int, startId: Int): Int {
        when (intent?.action) {
            ACTION_CAPTURE -> handleCaptureRequest()
            ACTION_STOP -> stopEverything()
            else -> addBubble()
        }
        return START_STICKY
    }

    // ---------------- Floating bubble ----------------

    private fun addBubble() {
        if (bubbleView != null) return

        val size = dp(56)
        val bubble = TextView(this).apply {
            text = "SS"
            setTextColor(Color.WHITE)
            gravity = Gravity.CENTER
            setTextSize(TypedValue.COMPLEX_UNIT_SP, 16f)
            background = GradientDrawable().apply {
                shape = GradientDrawable.OVAL
                setColor(Color.parseColor("#22C55E"))
            }
        }

        val params = WindowManager.LayoutParams(
            size, size,
            overlayType(),
            WindowManager.LayoutParams.FLAG_NOT_FOCUSABLE,
            android.graphics.PixelFormat.TRANSLUCENT
        ).apply {
            gravity = Gravity.TOP or Gravity.START
            x = dp(12)
            y = dp(240)
        }

        var initialX = 0
        var initialY = 0
        var touchX = 0f
        var touchY = 0f
        var moved = false

        bubble.setOnTouchListener { _, event ->
            when (event.action) {
                MotionEvent.ACTION_DOWN -> {
                    initialX = params.x
                    initialY = params.y
                    touchX = event.rawX
                    touchY = event.rawY
                    moved = false
                    true
                }
                MotionEvent.ACTION_MOVE -> {
                    val dx = (event.rawX - touchX).toInt()
                    val dy = (event.rawY - touchY).toInt()
                    if (kotlin.math.abs(dx) > dp(6) || kotlin.math.abs(dy) > dp(6)) moved = true
                    params.x = initialX + dx
                    params.y = initialY + dy
                    windowManager.updateViewLayout(bubble, params)
                    true
                }
                MotionEvent.ACTION_UP -> {
                    if (!moved) onBubbleTap()
                    true
                }
                else -> false
            }
        }

        bubbleView = bubble
        windowManager.addView(bubble, params)
    }

    private fun onBubbleTap() {
        if (projection != null) {
            // Already have a live projection: scan again without re-prompting.
            startService(Intent(this, OverlayService::class.java).setAction(ACTION_CAPTURE))
        } else {
            // First scan of the session: ask for screen-capture consent once.
            val i = Intent(this, ProjectionRequestActivity::class.java)
                .addFlags(Intent.FLAG_ACTIVITY_NEW_TASK)
            startActivity(i)
        }
    }

    // ---------------- Capture + analyze ----------------

    private fun handleCaptureRequest() {
        val existing = projection
        if (existing != null) {
            // Reuse the live projection; the bubble tap doesn't change the screen,
            // so a tiny delay is enough to let the tap ripple settle.
            captureFrom(existing, delayMs = 120)
            return
        }

        // No live projection yet: create one from the just-granted consent token.
        val data = MediaProjectionHolder.data
        if (data == null) {
            showToast("Screen capture not granted")
            return
        }
        val resultCode = MediaProjectionHolder.resultCode
        MediaProjectionHolder.clear()

        ensureForeground()
        val mpm = getSystemService(MEDIA_PROJECTION_SERVICE) as MediaProjectionManager
        val newProjection: MediaProjection = try {
            mpm.getMediaProjection(resultCode, data)
        } catch (e: Exception) {
            showToast("Couldn't start screen capture - tap the bubble to try again.")
            stopForegroundCompat()
            isForeground = false
            return
        }
        newProjection.registerCallback(object : MediaProjection.Callback() {
            override fun onStop() {
                // System or user revoked capture; drop it so the next tap re-prompts.
                projection = null
            }
        }, handler)
        projection = newProjection
        updateNotification()

        // First capture: wait for the consent dialog to dismiss so we grab the app
        // the user is on, not the SafeShop permission screen.
        captureFrom(newProjection, delayMs = 400)
    }

    private fun captureFrom(activeProjection: MediaProjection, delayMs: Long) {
        scope.launch {
            if (delayMs > 0) delay(delayMs)
            if (projection == null) return@launch
            val capture = ScreenCapture(activeProjection, resources.displayMetrics)
            capture.captureOnce { bitmap ->
                if (bitmap == null) {
                    showToast("Could not capture the screen")
                    return@captureOnce
                }
                scope.launch {
                    val text = try {
                        TextRecognizerHelper.recognizeBitmap(bitmap)
                    } catch (e: Exception) {
                        ""
                    }
                    when (val r = Analyzer.analyze(this@OverlayService, "Screen scan", text)) {
                        is AnalyzeResult.Success -> showResult(r.response)
                        is AnalyzeResult.Error -> showToast(r.message)
                    }
                }
            }
        }
    }

    // ---------------- Result card overlay ----------------

    private fun showResult(result: AnalyzeResponse) {
        removeCard()

        val owner = WindowLifecycleOwner().also { it.onCreate() }
        val compose = ComposeView(this)
        owner.attachTo(compose)

        val shown = mutableStateOf(true)
        compose.setContent {
            if (!shown.value) return@setContent
            SafeShopTheme {
                Box(
                    modifier = Modifier
                        .fillMaxSize()
                        .background(ComposeColor(0xCC000000))
                        .clickable { removeCard() }
                        .padding(16.dp),
                    contentAlignment = Alignment.Center
                ) {
                    Column(
                        modifier = Modifier
                            .fillMaxWidth()
                            .verticalScroll(rememberScrollState())
                    ) {
                        ScoreCard(result)
                        Spacer(Modifier.height(12.dp))
                        Button(onClick = { removeCard() }, modifier = Modifier.fillMaxWidth()) {
                            Text("Close")
                        }
                    }
                }
            }
        }

        val params = WindowManager.LayoutParams(
            WindowManager.LayoutParams.MATCH_PARENT,
            WindowManager.LayoutParams.MATCH_PARENT,
            overlayType(),
            WindowManager.LayoutParams.FLAG_NOT_FOCUSABLE,
            android.graphics.PixelFormat.TRANSLUCENT
        )

        cardView = compose
        cardOwner = owner
        windowManager.addView(compose, params)
    }

    private fun removeCard() {
        cardView?.let {
            try {
                windowManager.removeView(it)
            } catch (_: Exception) {
            }
        }
        cardOwner?.onDestroy()
        cardView = null
        cardOwner = null
    }

    // ---------------- Foreground service plumbing ----------------

    private fun ensureForeground() {
        if (isForeground) return
        val notification = buildNotification()
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.Q) {
            startForeground(
                NOTIFICATION_ID,
                notification,
                ServiceInfo.FOREGROUND_SERVICE_TYPE_MEDIA_PROJECTION
            )
        } else {
            startForeground(NOTIFICATION_ID, notification)
        }
        isForeground = true
    }

    private fun updateNotification() {
        if (!isForeground) return
        (getSystemService(NOTIFICATION_SERVICE) as NotificationManager)
            .notify(NOTIFICATION_ID, buildNotification())
    }

    private fun stopForegroundCompat() {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.N) {
            stopForeground(STOP_FOREGROUND_REMOVE)
        } else {
            @Suppress("DEPRECATION")
            stopForeground(true)
        }
        isForeground = false
    }

    /** Fully tears down the session: capture, bubble, foreground notification, service. */
    private fun stopEverything() {
        removeCard()
        projection?.stop()
        projection = null
        bubbleView?.let {
            try {
                windowManager.removeView(it)
            } catch (_: Exception) {
            }
        }
        bubbleView = null
        stopForegroundCompat()
        stopSelf()
    }

    private fun buildNotification(): Notification {
        val builder = if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            Notification.Builder(this, CHANNEL_ID)
        } else {
            @Suppress("DEPRECATION")
            Notification.Builder(this)
        }
        val ready = projection != null
        val stopIntent = PendingIntent.getService(
            this,
            0,
            Intent(this, OverlayService::class.java).setAction(ACTION_STOP),
            PendingIntent.FLAG_IMMUTABLE or PendingIntent.FLAG_UPDATE_CURRENT
        )
        return builder
            .setContentTitle("SafeShop")
            .setContentText(
                if (ready) "Screen access on - tap the bubble to scan any product."
                else "Reading the screen to score this product..."
            )
            .setSmallIcon(android.R.drawable.ic_menu_view)
            .setOngoing(true)
            .addAction(android.R.drawable.ic_menu_close_clear_cancel, "Stop", stopIntent)
            .build()
    }

    private fun createNotificationChannel() {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            val channel = NotificationChannel(
                CHANNEL_ID,
                getString(com.safeshop.app.R.string.overlay_channel_name),
                NotificationManager.IMPORTANCE_LOW
            )
            (getSystemService(NOTIFICATION_SERVICE) as NotificationManager)
                .createNotificationChannel(channel)
        }
    }

    private fun overlayType(): Int =
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            WindowManager.LayoutParams.TYPE_APPLICATION_OVERLAY
        } else {
            @Suppress("DEPRECATION")
            WindowManager.LayoutParams.TYPE_PHONE
        }

    private fun showToast(msg: String) {
        Toast.makeText(this, msg, Toast.LENGTH_SHORT).show()
    }

    private fun dp(value: Int): Int =
        (value * resources.displayMetrics.density).toInt()

    override fun onDestroy() {
        super.onDestroy()
        removeCard()
        projection?.stop()
        projection = null
        bubbleView?.let {
            try {
                windowManager.removeView(it)
            } catch (_: Exception) {
            }
        }
        bubbleView = null
        scope.cancel()
    }

    companion object {
        private const val CHANNEL_ID = "safeshop_overlay"
        private const val NOTIFICATION_ID = 1001
        const val ACTION_CAPTURE = "com.safeshop.app.action.CAPTURE"
        const val ACTION_STOP = "com.safeshop.app.action.STOP"

        fun start(context: Context) {
            context.startService(Intent(context, OverlayService::class.java))
        }

        fun requestCapture(context: Context) {
            context.startService(
                Intent(context, OverlayService::class.java).setAction(ACTION_CAPTURE)
            )
        }
    }
}
