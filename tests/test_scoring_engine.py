from backend.final_scoring_engine import final_score, get_verdict


def test_final_score_flags_unhealthy_processed_product():
    product = {
        "parsed_nutrition": {
            "energy_kcal": 420.0,
            "protein_g": 8.0,
            "carbohydrate_g": 65.0,
            "sugar_g": 5.0,
            "added_sugar_g": 0.0,
            "fat_g": 12.0,
            "saturated_fat_g": 4.0,
            "trans_fat_g": 0.0,
            "fiber_g": 1.0,
            "sodium_mg": 980.0,
            "confidence": 1.0,
            "raw_text": "Energy 420 kcal Sodium 980 mg"
        },
        "ingredient_analysis": {
            "additives": {
                "primary": [
                    {
                        "code": "ins621",
                        "name": "Monosodium glutamate",
                        "risk": "moderate",
                        "category": "flavour_enhancer"
                    }
                ],
                "secondary": [],
                "generic": []
            },
            "msg": True,
            "sweeteners": [],
            "processed_oils": ["palm oil"],
            "ultra_processed": True,
            "artificial_colors": []
        }
    }

    score, reasons = final_score(product)

    assert score < 40
    assert get_verdict(score) == "Unhealthy"
    assert "High salt (can increase BP)" in reasons
    assert "Highly processed product" in reasons
