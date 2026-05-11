import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor
import joblib

df = pd.read_csv("ml_food_dataset.csv")

X = df.drop(columns=["score"])
y = df["score"]

X_train,X_test,y_train,y_test = train_test_split(
    X,y,test_size=0.2,random_state=42
)

model = RandomForestRegressor(
    n_estimators=300,
    max_depth=12
)

model.fit(X_train,y_train)

print("Training complete")

score = model.score(X_test,y_test)

print("Model R²:",score)

joblib.dump(model,"health_model.pkl")