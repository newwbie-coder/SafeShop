from ocr_layer.section_detector import split_label_text
from ocr_layer.text_cleaner import clean_text


def test_split_finds_ingredients_and_nutrition():
    text = (
        "Ingredients: refined wheat flour, palm oil, salt. "
        "Nutrition: Energy 425 kcal Protein 11 g Sodium 1583 mg"
    )
    ingredients, nutrition = split_label_text(text)
    assert "palm oil" in ingredients
    assert "425" in nutrition


def test_split_falls_back_when_no_headers():
    nutrition_only = "Energy 389 kcal Protein 16.9 g Carbohydrate 66.3 g Sodium 2 mg"
    ingredients, nutrition = split_label_text(nutrition_only)
    assert ingredients == ""
    assert "389" in nutrition

    ingredient_only = "whole wheat flour, oats, almonds, salt, sunflower oil and milk solids"
    ingredients, nutrition = split_label_text(ingredient_only)
    assert "oats" in ingredients
    assert nutrition == ""


def test_split_empty_stays_empty():
    ingredients, nutrition = split_label_text("")
    assert ingredients == ""
    assert nutrition == ""


def test_split_headerless_mixed_label():
    text = "wheat flour, palm oil, salt energy 425 kcal protein 11 g sodium 1583 mg"
    ingredients, nutrition = split_label_text(text)
    assert "palm oil" in ingredients
    assert "425" in nutrition


def test_contains_line_is_not_treated_as_ingredients_header():
    text = "Contains: milk. Energy 389 kcal Protein 16.9 g"
    ingredients, nutrition = split_label_text(text)
    assert "389" in nutrition
    assert ingredients == ""


def test_cleaner_fixes_common_ocr_typos():
    cleaned = clean_text("1ngredients wheat flour Nutritlon Energy 389 kcal Proteln 16.9 Sodlum 2")
    assert "ingredients" in cleaned
    assert "nutrition" in cleaned
    assert "protein" in cleaned
    assert "sodium" in cleaned
