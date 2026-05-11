import json
import joblib
import pandas as pd

model = joblib.load("health_model.pkl")

INPUT = "parsed_dataset_v8_2.jsonl"
OUTPUT = "ml_scored_dataset_new.jsonl"


def extract_features(p):

    n = p.get("parsed_nutrition",{})
    a = p.get("ingredient_analysis",{})

    return {

        "energy": n.get("energy_kcal",0) or 0,
        "protein": n.get("protein_g",0) or 0,
        "carbs": n.get("carbohydrate_g",0) or 0,
        "sugar": n.get("sugar_g",0) or 0,
        "added_sugar": n.get("added_sugar_g",0) or 0,
        "fat": n.get("fat_g",0) or 0,
        "sat_fat": n.get("saturated_fat_g",0) or 0,
        "trans_fat": n.get("trans_fat_g",0) or 0,
        "fiber": n.get("fiber_g",0) or 0,
        "sodium": n.get("sodium_mg",0) or 0,

        "msg": int(a.get("msg",False)),
        "sweeteners": len(a.get("sweeteners",[])),
        "artificial_colors": len(a.get("artificial_colors",[])),
        "processed_oils": len(a.get("processed_oils",[])),
        "ultra_processed": int(a.get("ultra_processed",False))
    }


with open(INPUT) as infile, open(OUTPUT,"w") as outfile:

    for line in infile:

        product = json.loads(line)

        features = extract_features(product)

        df = pd.DataFrame([features])

        score = model.predict(df)[0]

        score = max(0,min(100,round(score,2)))

        product["ml_health_score"] = score

        outfile.write(json.dumps(product)+"\n")