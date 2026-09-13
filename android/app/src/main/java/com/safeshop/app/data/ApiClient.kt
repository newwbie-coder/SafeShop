package com.safeshop.app.data

import okhttp3.OkHttpClient
import okhttp3.logging.HttpLoggingInterceptor
import retrofit2.Retrofit
import retrofit2.converter.gson.GsonConverterFactory
import java.util.concurrent.TimeUnit

object ApiClient {

    @Volatile
    private var currentUrl: String? = null

    @Volatile
    private var cachedApi: SafeShopApi? = null

    /** Returns a SafeShopApi bound to [baseUrl], rebuilding only when the URL changes. */
    @Synchronized
    fun api(baseUrl: String): SafeShopApi {
        val existing = cachedApi
        if (existing != null && currentUrl == baseUrl) return existing

        val logging = HttpLoggingInterceptor().apply {
            level = HttpLoggingInterceptor.Level.BASIC
        }
        val client = OkHttpClient.Builder()
            .addInterceptor(logging)
            .connectTimeout(15, TimeUnit.SECONDS)
            .readTimeout(30, TimeUnit.SECONDS)
            .build()

        val api = Retrofit.Builder()
            .baseUrl(baseUrl)
            .client(client)
            .addConverterFactory(GsonConverterFactory.create())
            .build()
            .create(SafeShopApi::class.java)

        cachedApi = api
        currentUrl = baseUrl
        return api
    }
}
