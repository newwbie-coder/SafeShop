from backend.final_scoring_engine import final_score, get_verdict
from backend.main import score_product
from backend.nutrition_parser4 import parse_nutrition


CHINGS_ING = (
    "Refined Wheat Flour (Maida), Refined Palm Oil, Iodised Salt, Wheat Gluten, "
    "Thickener (INS 508), Stabilizer (INS 451), Acidity Regulator (INS 501(i)), "
    "Raising Agent (INS 500(ii)), Antioxidant (INS 319), Corn Starch, Iodised Salt, "
    "Dehydrated Garlic, Sugar, Mixed Spices [Chilli, Ginger, Pepper], Onion Powder, "
    "Dehydrated Vegetables [Carrot, Parsley], Flavour Enhancer (INS 635), "
    "Soy Sauce Powder (Soybean, Wheat, Salt), Acidity Regulator (INS 330), "
    "Sunflower Oil, Anticaking Agent (INS 551), Colour (INS 160c (i)), Tomato Powder, "
    "Dehydrated Herb, Yeast Extract"
)
CHINGS_NUT = (
    "Nutrition_per: 100 g\nServing_Size: 60g\nEnergy (kcal): 425\nProtein (g): 11.0\n"
    "Carbohydrate (g): 63.8\nDietary Fibre (g): 8.1\nTotal Sugars (g): 2.6\n"
    "Added Sugars (g): 2.6\nTotal Fat (g): 14.0\nSaturated Fat (g): 7.1\n"
    "Trans Fat (g): 0.0\nSodium (mg): 1583"
)

CHOCOS_ING = (
    "MULTIGRAIN FLOUR MIX (64.8%), {WHEAT FLOUR (ATTA) (55.8%), SORGHUM (JOWAR) FLOUR (3%), "
    "RICE FLOUR (3%), CORN MEAL (3%)}, SUGAR, COCOA SOLIDS (5.3%), MINERALS, CEREAL EXTRACT, "
    "IODIZED SALT, COLOURS (INS 150a, INS 150d), EDIBLE VEGETABLE OIL (PALMOLEIN), "
    "FLAVOURS (NATURE IDENTICAL & ARTIFICIAL (CREAM)), VITAMINS, ANTIOXIDANT (INS 307b)"
)
CHOCOS_NUT = (
    "Nutrition_per: 100 g\nServing_Size: 30 g\nENERGY: 373 kcal\nENERGY FROM FAT: 27 kcal\n"
    "TOTAL FAT: 3.0 g\nSATURATED FATTY ACIDS: 1.2 g\nTRANS FATTY ACIDS: 0 g\n"
    "TOTAL CARBOHYDRATES: 81.0 g\nOF WHICH TOTAL SUGARS: 27.5 g\nOF WHICH ADDED SUGARS: 27.0 g\n"
    "OF WHICH DIETARY FIBRE: 7.0 g\nPROTEIN: 9.0 g\nSODIUM: 250 mg"
)

JAGGERY_NUT = (
    "Nutrition_per: 10g\nServing_Size: 10g\nEnergy: 37 kcal\nProtein: 0g\n"
    "Carbohydrate: 9g\nTotal Sugar (Natural): 9.2g\nAdded Sugar: 0g\n"
    "Dietary Fibre: 0g\nSodium: 0 mg\nTotal Fat: 0g\nSaturated Fat: 0g\nTrans Fat: 0g"
)

FIVE_STAR_ING = (
    "Sugar, Liquid Glucose, Milk Solids, Invert Sugar, Hydrogenated Oil, Cocoa Butter, "
    "Cocoa Solids, Fractionated Fat, Emulsifiers (442, 476), Hydrolyzed Vegetable Protein, "
    "Salt, Flavour"
)
FIVE_STAR_NUT = (
    "Nutrition_per: 100g\nServing_Size: 35.2g\nEnergy: 444kcal\nProtein: 3.3g\n"
    "Carbohydrate: 72.9g\nTotal Sugars: 55.5g\nAdded Sugars: 52.6g\nTotal Fat: 15.9g\n"
    "Saturated Fat: 10.1g\nTrans Fat: 0.1g\nCholesterol: 4.9mg\nSodium: 170.0mg"
)

DARK90_ING = "Cocoa Solids, Cocoa Butter, Sugar, Emulsifier (E322), Flavour"
DARK90_NUT = (
    "Nutrition_per: 100g\nEnergy, kcal: 554 kcal\nTotal Fat, g: 36.1 g\n"
    "Saturated Fat, g: 21.5 g\nTrans Fat, g: 0 g\nTotal Carbohydrate, g: 43.0 g\n"
    "Added Sugar, g: 10.0 g\nProtein, g: 14.2 g"
)

REDBULL_ING = (
    "Water, Sucrose, Glucose, Acidity Regulator, Carbon Dioxide, Taurine, Flavour, "
    "Colour, Caffeine, Vitamins"
)
REDBULL_NUT = (
    "Nutrition Information (Per 100 ml) Serving Size: 250 ml Energy: 45 kcal Fat: 0 g "
    "Carbohydrate: 11 g Sugars: 11 g Protein: 0 g Sodium: 41 mg Caffeine: 30 mg"
)

MENTOS_FAKE_NUT = (
    "Sugar, Liquid Glucose, Fruit Juice (2%), Acidity Regulator (INS 330), Starch, "
    "Hydrogenated Vegetable Oil, Thickener (INS 414), Emulsifier (INS 471) "
    "Contains Permitted Synthetic Food Colour (INS 110)"
)

OATS_ING = "Whole grain oats"
OATS_NUT = (
    "Nutrition_per: 100 g Energy: 389 kcal Protein: 16.9 g Carbohydrate: 66.3 g "
    "Total Sugars: 1.2 g Added Sugars: 0 g Dietary Fibre: 10.6 g Total Fat: 6.9 g "
    "Saturated Fat: 1.2 g Trans Fat: 0 g Sodium: 2 mg"
)


def test_parse_chings_gets_fiber_and_sugar():
    parsed = parse_nutrition(CHINGS_NUT)
    assert parsed["energy_kcal"] == 425
    assert parsed["sugar_g"] == 2.6
    assert parsed["fiber_g"] == 8.1
    assert parsed["sodium_mg"] == 1583
    assert parsed["energy_kcal"] != 2000


def test_parse_jaggery_scales_to_100g():
    parsed = parse_nutrition(JAGGERY_NUT)
    assert parsed["basis_g"] == 10
    assert parsed["energy_kcal"] == 370
    assert parsed["sugar_g"] == 92


def test_parse_ignores_rda_2000_kcal():
    parsed = parse_nutrition(
        "Nutrition_per: 100 g Energy Value (kcal): 372.5 Protein (g): 8.7 "
        "Carbohydrate (g): 85 Total Fat (g): 0.7 RDA: Guideline Daily Amount of an "
        "average adult (based on 2000 kcal diet)"
    )
    assert parsed["energy_kcal"] == 372.5


def test_parse_rejects_ingredient_list_as_nutrition():
    parsed = parse_nutrition(MENTOS_FAKE_NUT)
    assert parsed.get("confidence", 0) == 0
    assert parsed.get("sugar_g") in (None, 0) or parsed.get("confidence") == 0


def test_chings_noodles_unhealthy():
    result = score_product(CHINGS_ING, CHINGS_NUT)
    assert result["verdict"] == "Unhealthy"
    assert result["score"] < 40
    assert result["flags"]["msg"] is True


def test_chocos_unhealthy():
    result = score_product(CHOCOS_ING, CHOCOS_NUT)
    assert result["verdict"] == "Unhealthy"
    assert result["score"] < 45


def test_five_star_unhealthy():
    result = score_product(FIVE_STAR_ING, FIVE_STAR_NUT)
    assert result["verdict"] == "Unhealthy"
    assert result["score"] < 40


def test_jaggery_not_healthy_100():
    result = score_product("", JAGGERY_NUT)
    assert result["verdict"] != "Healthy"
    assert result["score"] < 70


def test_90_percent_dark_not_as_bad_as_candy():
    dark = score_product(DARK90_ING, DARK90_NUT)
    candy = score_product(FIVE_STAR_ING, FIVE_STAR_NUT)
    assert dark["score"] > candy["score"]
    assert dark["verdict"] in ("Moderate", "Unhealthy")


def test_red_bull_unhealthy():
    result = score_product(REDBULL_ING, REDBULL_NUT)
    assert result["verdict"] == "Unhealthy"
    assert result["score"] < 40


def test_mentos_not_scored_healthy_from_swapped_fields():
    result = score_product("", MENTOS_FAKE_NUT)
    assert result["verdict"] != "Healthy"
    assert result["score"] < 70


def test_plain_oats_healthy_or_high_moderate():
    result = score_product(OATS_ING, OATS_NUT)
    assert result["score"] >= 55
    assert result["verdict"] in ("Healthy", "Moderate")


def test_kj_energy_uses_kcal_not_kilojoules():
    parsed = parse_nutrition(
        "Nutrition per gram: 100g Energy: 990 kJ/(233 kcal) Carbohydrate: 60 g Of which Sugars: 53 g"
    )
    assert parsed["energy_kcal"] == 233
    assert parsed["sugar_g"] == 53


def test_honey_sugar_not_zero_when_total_listed():
    parsed = parse_nutrition(
        "Nutrition per gram/ml: 100g Energy (kcal): 328 Carbohydrate (g): 82 "
        "Added sugar (g): 0 Total sugar (g): 82 Protein (g): 0.25 Total fat (g): 0"
    )
    assert parsed["sugar_g"] == 82
    assert parsed["added_sugar_g"] == 0


def test_honey_not_healthy():
    result = score_product(
        "",
        "Nutrition per gram/ml: 100g Energy (kcal): 328 Carbohydrate (g): 82 "
        "Added sugar (g): 0 Total sugar (g): 82 Protein (g): 0.25 Total fat (g): 0",
    )
    assert result["verdict"] != "Healthy"
    assert result["score"] < 70
