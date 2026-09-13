package com.safeshop.app

import android.app.Activity
import android.content.ClipData
import android.content.ClipboardManager
import android.content.Context
import android.graphics.Color
import android.os.Bundle
import android.util.TypedValue
import android.widget.Button
import android.widget.LinearLayout
import android.widget.ScrollView
import android.widget.TextView
import android.widget.Toast

/** Plain-view screen (no Compose, runs in its own process) that shows a crash trace. */
class CrashActivity : Activity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        val trace = intent.getStringExtra(EXTRA_TRACE) ?: "No crash details available."
        val pad = (16 * resources.displayMetrics.density).toInt()

        val root = LinearLayout(this).apply {
            orientation = LinearLayout.VERTICAL
            setBackgroundColor(Color.parseColor("#0B0B0B"))
            setPadding(pad, pad, pad, pad)
        }
        val title = TextView(this).apply {
            text = "SafeShop crashed"
            setTextColor(Color.parseColor("#F87171"))
            setTextSize(TypedValue.COMPLEX_UNIT_SP, 18f)
        }
        val hint = TextView(this).apply {
            text = "Tap Copy, then paste this to share so it can be fixed."
            setTextColor(Color.parseColor("#B3FFFFFF"))
            setTextSize(TypedValue.COMPLEX_UNIT_SP, 12f)
            setPadding(0, pad / 2, 0, pad / 2)
        }
        val copyBtn = Button(this).apply {
            text = "Copy crash details"
            setOnClickListener {
                val cm = getSystemService(Context.CLIPBOARD_SERVICE) as ClipboardManager
                cm.setPrimaryClip(ClipData.newPlainText("SafeShop crash", trace))
                Toast.makeText(this@CrashActivity, "Copied", Toast.LENGTH_SHORT).show()
            }
        }
        val body = TextView(this).apply {
            text = trace
            setTextColor(Color.parseColor("#E5E7EB"))
            setTextIsSelectable(true)
            setTextSize(TypedValue.COMPLEX_UNIT_SP, 11f)
            setPadding(0, pad, 0, pad)
        }
        val scroll = ScrollView(this).apply { addView(body) }

        root.addView(title)
        root.addView(hint)
        root.addView(copyBtn)
        root.addView(scroll)
        setContentView(root)
    }

    companion object {
        const val EXTRA_TRACE = "trace"
    }
}
