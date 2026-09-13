package com.safeshop.app.data

import android.content.Context

/**
 * Thin repository around the backend. Both capture paths (live camera and the
 * screen-capture overlay) produce a raw OCR text blob and call [analyze].
 */
sealed class AnalyzeResult {
    data class Success(val response: AnalyzeResponse) : AnalyzeResult()
    data class Error(val message: String) : AnalyzeResult()
}

object Analyzer {
    suspend fun analyze(context: Context, name: String, rawText: String): AnalyzeResult {
        if (rawText.isBlank()) {
            return AnalyzeResult.Error("No text detected. Point at the label and try again.")
        }
        return try {
            val api = ApiClient.api(BackendConfig.getBaseUrl(context))
            val response = api.analyzeText(AnalyzeTextRequest(name = name, rawText = rawText))
            AnalyzeResult.Success(response)
        } catch (e: Exception) {
            AnalyzeResult.Error(e.message ?: "Analysis failed")
        }
    }
}
