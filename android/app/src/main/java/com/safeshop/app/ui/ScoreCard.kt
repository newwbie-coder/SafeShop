package com.safeshop.app.ui

import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.Canvas
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.geometry.Size
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.drawscope.Stroke
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.safeshop.app.data.AnalyzeResponse
import kotlin.math.roundToInt

private val Green = Color(0xFF22C55E)
private val Amber = Color(0xFFF59E0B)
private val Red = Color(0xFFEF4444)
private val CardBg = Color(0xFF141414)
private val SubtleBg = Color(0x0FFFFFFFF)

private data class Level(val label: String, val fraction: Float)

private fun scoreColor(score: Double): Color = when {
    score >= 70 -> Green
    score >= 40 -> Amber
    else -> Red
}

private fun riskColor(risk: String): Color = when (risk.lowercase()) {
    "high" -> Color(0xFFFF4D4F)
    "medium", "moderate" -> Color(0xFFFFB300)
    else -> Color(0xFF52C41A)
}

private fun levelFor(value: Double, type: String): Level = when (type) {
    "sodium" -> when {
        value > 500 -> Level("High", 1f)
        value > 200 -> Level("Medium", 0.6f)
        else -> Level("Low", 0.3f)
    }
    "sugar" -> when {
        value > 20 -> Level("High", 1f)
        value > 10 -> Level("Medium", 0.6f)
        else -> Level("Low", 0.3f)
    }
    else -> when { // fat
        value > 10 -> Level("High", 1f)
        value > 5 -> Level("Medium", 0.6f)
        else -> Level("Low", 0.3f)
    }
}

private fun levelColor(label: String): Color = when (label) {
    "High" -> Red
    "Medium" -> Amber
    else -> Green
}

/** Ported from extension/content.js getDynamicAdvice(). */
private fun dynamicAdvice(result: AnalyzeResponse): List<String> {
    val advice = mutableListOf<String>()
    val reasons = result.reasons.joinToString(" ").lowercase()

    if (reasons.contains("trans fat")) {
        advice.add("Avoid frequent consumption (heart risk)")
        advice.add("Very occasional intake only")
    }
    if (reasons.contains("high sodium") || reasons.contains("high salt")) {
        advice.add("Limit intake (BP risk)")
    }
    if (result.flags?.msg == true) {
        advice.add("Contains flavour enhancers (may trigger sensitivity)")
    }
    if (result.flags?.ultraProcessed == true) {
        advice.add("Highly processed - avoid daily consumption")
    }
    val additivesCount = (result.additives?.primary?.size ?: 0) +
        (result.additives?.generic?.size ?: 0)
    if (additivesCount > 5) {
        advice.add("Contains many additives - prefer natural foods")
    }
    if (advice.isEmpty()) {
        advice.add(if (result.score < 40) "Occasional consumption recommended" else "Safe in moderation")
    }
    return advice
}

@Composable
fun ScoreCard(result: AnalyzeResponse, modifier: Modifier = Modifier) {
    val color = scoreColor(result.score)
    val nutrition = result.parsedNutrition

    Column(
        modifier = modifier
            .fillMaxWidth()
            .clip(RoundedCornerShape(16.dp))
            .background(CardBg)
            .padding(16.dp)
    ) {
        // Header: score ring + verdict
        Row(verticalAlignment = Alignment.CenterVertically) {
            Box(contentAlignment = Alignment.Center, modifier = Modifier.size(56.dp)) {
                Canvas(modifier = Modifier.size(56.dp)) {
                    val stroke = 7.dp.toPx()
                    val arcSize = Size(size.width - stroke, size.height - stroke)
                    val topLeft = androidx.compose.ui.geometry.Offset(stroke / 2, stroke / 2)
                    drawArc(
                        color = Color(0x22FFFFFF),
                        startAngle = 0f,
                        sweepAngle = 360f,
                        useCenter = false,
                        topLeft = topLeft,
                        size = arcSize,
                        style = Stroke(width = stroke)
                    )
                    drawArc(
                        color = color,
                        startAngle = -90f,
                        sweepAngle = (result.score.toFloat().coerceIn(0f, 100f) / 100f) * 360f,
                        useCenter = false,
                        topLeft = topLeft,
                        size = arcSize,
                        style = Stroke(width = stroke)
                    )
                }
                Text(
                    text = result.score.roundToInt().toString(),
                    color = Color.White,
                    fontSize = 14.sp,
                    fontWeight = FontWeight.Bold
                )
            }
            Column(modifier = Modifier.padding(start = 12.dp)) {
                Text("Safe Score", color = Color.White, fontWeight = FontWeight.SemiBold, fontSize = 15.sp)
                Text(result.verdict, color = color, fontSize = 13.sp, fontWeight = FontWeight.Medium)
            }
        }

        // Health risks
        val riskMessages = result.healthFlags.map { it.message }
        SectionCard("Health Risks", riskMessages, titleColor = Color(0xFFF87171))

        // Nutrition impact bars
        if (nutrition != null) {
            Column(
                modifier = Modifier
                    .fillMaxWidth()
                    .padding(top = 10.dp)
                    .clip(RoundedCornerShape(10.dp))
                    .background(SubtleBg)
                    .padding(10.dp)
            ) {
                Text("Nutrition Impact", color = Color.White, fontWeight = FontWeight.SemiBold, fontSize = 12.sp)
                NutritionBar("Sodium", levelFor(nutrition.sodiumMg ?: 0.0, "sodium"))
                NutritionBar("Sugar", levelFor(nutrition.sugarG ?: 0.0, "sugar"))
                NutritionBar("Fat", levelFor(nutrition.saturatedFatG ?: 0.0, "fat"))
            }
        }

        // Key issues (top 3 reasons)
        SectionCard("Key Issues", result.reasons.take(3))

        // Advice
        SectionCard("Advice", dynamicAdvice(result))

        // Additives
        val additives = (result.additives?.primary ?: emptyList()) +
            (result.additives?.generic ?: emptyList())
        if (additives.isNotEmpty()) {
            Column(
                modifier = Modifier
                    .fillMaxWidth()
                    .padding(top = 10.dp)
                    .clip(RoundedCornerShape(10.dp))
                    .background(SubtleBg)
                    .padding(10.dp)
            ) {
                Text("Additives (${additives.size})", color = Color.White, fontWeight = FontWeight.SemiBold, fontSize = 12.sp)
                additives.forEach { a ->
                    val label = if (a.code.isNullOrBlank()) a.name else "${a.name} (${a.code.uppercase()})"
                    Text(
                        label,
                        color = riskColor(a.risk),
                        fontSize = 12.sp,
                        modifier = Modifier.padding(top = 3.dp)
                    )
                }
            }
        }
    }
}

@Composable
private fun SectionCard(title: String, items: List<String>, titleColor: Color = Color.White) {
    if (items.isEmpty()) return
    Column(
        modifier = Modifier
            .fillMaxWidth()
            .padding(top = 10.dp)
            .clip(RoundedCornerShape(10.dp))
            .background(SubtleBg)
            .padding(10.dp)
    ) {
        Text(title, color = titleColor, fontWeight = FontWeight.SemiBold, fontSize = 12.sp)
        items.forEach {
            Text(it, color = Color(0xCCFFFFFF), fontSize = 12.sp, modifier = Modifier.padding(top = 3.dp))
        }
    }
}

@Composable
private fun NutritionBar(label: String, level: Level) {
    Column(modifier = Modifier.padding(top = 6.dp)) {
        Text("$label - ${level.label}", color = Color(0xB3FFFFFF), fontSize = 11.sp)
        Box(
            modifier = Modifier
                .fillMaxWidth()
                .height(6.dp)
                .clip(RoundedCornerShape(6.dp))
                .background(Color(0x14FFFFFF))
        ) {
            Box(
                modifier = Modifier
                    .fillMaxWidth(level.fraction)
                    .height(6.dp)
                    .clip(RoundedCornerShape(6.dp))
                    .background(levelColor(level.label))
            )
        }
    }
}
