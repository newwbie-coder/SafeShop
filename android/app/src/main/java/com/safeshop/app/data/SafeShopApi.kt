package com.safeshop.app.data

import retrofit2.http.Body
import retrofit2.http.POST

interface SafeShopApi {
    @POST("analyze_text")
    suspend fun analyzeText(@Body body: AnalyzeTextRequest): AnalyzeResponse
}
