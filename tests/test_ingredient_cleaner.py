from backend.ingredient_cleaner import clean_ingredients


def test_clean_ingredients_normalizes_common_noise():
    cleaned = clean_ingredients([
        "contains sugar",
        "vegetable oils",
        "milk chocolate"
    ])

    assert "sugar" in cleaned
    assert "vegetable oil" in cleaned
    assert "milk chocolate" in cleaned
