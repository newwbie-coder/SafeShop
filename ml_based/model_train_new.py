import json
import pandas as pd

INPUT = "parsed_dataset_v8_2.jsonl"
OUTPUT = "ml_dataset_v2.csv"

rows = []

with open(INPUT, "r", encoding="utf-8") as f:
    for line in f:
        p = json.loads(line)

        n = p.get("parsed_nutrition", {})
        a = p.get("ingredient_analysis", {})

        # skip if no nutrition
        if not n:
            continue

        row = {
            # nutrition
            "energy": n.get("energy_kcal", 0) or 0,
            "protein": n.get("protein_g", 0) or 0,
            "carbs": n.get("carbohydrate_g", 0) or 0,
            "sugar": n.get("sugar_g", 0) or 0,
            "added_sugar": n.get("added_sugar_g", 0) or 0,
            "fat": n.get("fat_g", 0) or 0,
            "sat_fat": n.get("saturated_fat_g", 0) or 0,
            "trans_fat": n.get("trans_fat_g", 0) or 0,
            "fiber": n.get("fiber_g", 0) or 0,
            "sodium": n.get("sodium_mg", 0) or 0,

            # ingredient signals
            "msg": int(a.get("msg", False)),
            "sweeteners": len(a.get("sweeteners", [])),
            "colors": len(a.get("artificial_colors", [])),
            "processed_oils": len(a.get("processed_oils", [])),
            "ultra_processed": int(a.get("ultra_processed", False)),
        }

        rows.append(row)

df = pd.DataFrame(rows)
df.to_csv(OUTPUT, index=False)

print("✅ Dataset ready:", len(df))