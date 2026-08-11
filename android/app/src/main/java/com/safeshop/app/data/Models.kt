package com.safeshop.app.data

import com.google.gson.annotations.SerializedName

data class AnalyzeTextRequest(
    val name: String,
    @SerializedName("raw_text") val rawText: String
)

data class AnalyzeResponse(
    val score: Double = 0.0,
    val verdict: String = "",
    val reasons: List<String> = emptyList(),
    @SerializedName("parsed_nutrition") val parsedNutrition: ParsedNutrition? = null,
    @SerializedName("health_flags") val healthFlags: List<HealthFlag> = emptyList(),
    val confidence: Double = 0.0,
    val additives: Additives? = null,
    val flags: Flags? = null,
    val extracted: Extracted? = null
)

data class ParsedNutrition(
    @SerializedName("energy_kcal") val energyKcal: Double? = null,
    @SerializedName("protein_g") val proteinG: Double? = null,
    @SerializedName("carbohydrate_g") val carbohydrateG: Double? = null,
    @SerializedName("sugar_g") val sugarG: Double? = null,
    @SerializedName("saturated_fat_g") val saturatedFatG: Double? = null,
    @SerializedName("sodium_mg") val sodiumMg: Double? = null
)

data class HealthFlag(
    val type: String = "",
    val message: String = ""
)

data class Additive(
    val code: String? = null,
    val name: String = "",
    val risk: String = "unknown",
    val category: String? = null
)

data class Additives(
    val primary: List<Additive> = emptyList(),
    val secondary: List<Additive> = emptyList(),
    val generic: List<Additive> = emptyList()
)

data class Flags(
    val msg: Boolean = false,
    @SerializedName("ultra_processed") val ultraProcessed: Boolean = false,
    val sweeteners: List<String> = emptyList()
)

data class Extracted(
    val ingredients: String = "",
    @SerializedName("nutrition_text") val nutritionText: String = ""
)
