from backend.nutrition_parser4 import parse_nutrition


def test_parse_nutrition_extracts_core_fields():
    result = parse_nutrition(
        "Energy 425 kcal, Protein 6 g, Carbohydrate 70 g, Sugars 24 g, Sodium 620 mg"
    )

    assert result["energy_kcal"] == 425.0
    assert result["protein_g"] == 6.0
    assert result["carbohydrate_g"] == 70.0
    assert result["sugar_g"] == 24.0
    assert result["sodium_mg"] == 620.0
    assert result["confidence"] >= 0.75
