import joblib

model = joblib.load("health_model_v2.pkl")


def predict_score(n, a):

    features = [[
        n.get("energy_kcal", 0) or 0,
        n.get("protein_g", 0) or 0,
        n.get("carbohydrate_g", 0) or 0,
        n.get("sugar_g", 0) or 0,
        n.get("added_sugar_g", 0) or 0,
        n.get("fat_g", 0) or 0,
        n.get("saturated_fat_g", 0) or 0,
        n.get("trans_fat_g", 0) or 0,
        n.get("fiber_g", 0) or 0,
        n.get("sodium_mg", 0) or 0,

        int(a.get("msg", False)),
        len(a.get("sweeteners", [])),
        len(a.get("artificial_colors", [])),
        len(a.get("processed_oils", [])),
        int(a.get("ultra_processed", False))
    ]]

    score = model.predict(features)[0]

    return round(score, 2)