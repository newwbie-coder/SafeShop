import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor
import joblib

INPUT = "ml_dataset_labeled.csv"
MODEL_OUT = "health_model_v2.pkl"

# load
df = pd.read_csv(INPUT)

# split features & label
X = df.drop(columns=["label"])
y = df["label"]

# train-test split
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42
)

# model
model = RandomForestRegressor(n_estimators=100)

model.fit(X_train, y_train)

# evaluate
score = model.score(X_test, y_test)

print("✅ Model trained")
print("R2 Score:", round(score, 3))

# save
joblib.dump(model, MODEL_OUT)

print("📦 Model saved as:", MODEL_OUT)