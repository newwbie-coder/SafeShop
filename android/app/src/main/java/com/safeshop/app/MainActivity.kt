package com.safeshop.app

import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import com.safeshop.app.ui.AppRoot
import com.safeshop.app.ui.theme.SafeShopTheme

class MainActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContent {
            SafeShopTheme {
                AppRoot()
            }
        }
    }
}
