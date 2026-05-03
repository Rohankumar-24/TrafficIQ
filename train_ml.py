import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import accuracy_score, classification_report, mean_absolute_error, r2_score
import joblib
import os

#  Load CSV 
df = pd.read_csv("data/traffic_counts.csv")
print("Dataset loaded!")
print(f"Total records: {len(df)}")
print(df.head())

#  Feature Engineering
# Encode lane names to numbers (North=0, South=1, East=2, West=3)
le_lane = LabelEncoder()
df["lane_encoded"] = le_lane.fit_transform(df["lane"])

# Encode congestion labels to numbers
le_congestion = LabelEncoder()
df["congestion_encoded"] = le_congestion.fit_transform(df["congestion"])

print(f"\nLane classes   : {list(le_lane.classes_)}")
print(f"Congestion classes: {list(le_congestion.classes_)}")

#  Define Features (X) and Targets (y) 
# Features we use to make predictions
X = df[["vehicle_count", "hour", "lane_encoded"]]

# Target 1 — congestion level (Low/Medium/High)
y_class = df["congestion_encoded"]

# Target 2 — signal duration in seconds
y_reg = df["signal_duration"]

#  Train / Test Split 
X_train, X_test, y_class_train, y_class_test = train_test_split(
    X, y_class, test_size=0.2, random_state=42
)
_, _, y_reg_train, y_reg_test = train_test_split(
    X, y_reg, test_size=0.2, random_state=42
)

print(f"\nTraining samples : {len(X_train)}")
print(f"Testing samples  : {len(X_test)}")

# Model 1: Random Forest Classifier 
print("\n--- Training Congestion Classifier ---")
clf = RandomForestClassifier(n_estimators=100, random_state=42)
clf.fit(X_train, y_class_train)

y_pred_class = clf.predict(X_test)
acc = accuracy_score(y_class_test, y_pred_class)
print(f"Accuracy: {acc * 100:.2f}%")
print("\nClassification Report:")
print(classification_report(
    y_class_test, y_pred_class,
    target_names=le_congestion.classes_
))

# Model 2: Random Forest Regressor 
print("\n--- Training Signal Duration Regressor ---")
reg = RandomForestRegressor(n_estimators=100, random_state=42)
reg.fit(X_train, y_reg_train)

y_pred_reg = reg.predict(X_test)
mae = mean_absolute_error(y_reg_test, y_pred_reg)
r2  = r2_score(y_reg_test, y_pred_reg)
print(f"Mean Absolute Error : {mae:.2f} seconds")
print(f"R² Score            : {r2:.4f}")

#  Save Both Models + Encoders 
os.makedirs("models", exist_ok=True)

joblib.dump(clf,          "models/classifier.pkl")
joblib.dump(reg,          "models/regressor.pkl")
joblib.dump(le_lane,      "models/le_lane.pkl")
joblib.dump(le_congestion,"models/le_congestion.pkl")

print("\n All models saved to models/ folder:")
print("   - models/classifier.pkl")
print("   - models/regressor.pkl")
print("   - models/le_lane.pkl")
print("   - models/le_congestion.pkl")

#  Quick Test Prediction 
print("\n--- Quick Live Prediction Test ---")
# Simulate: North lane, 10 vehicles, hour 8 (morning rush)
test_input = pd.DataFrame([[10, 8, le_lane.transform(["North"])[0]]],
                           columns=["vehicle_count", "hour", "lane_encoded"])

pred_congestion = le_congestion.inverse_transform(clf.predict(test_input))[0]
pred_duration   = reg.predict(test_input)[0]

print(f"Input  → Lane: North | Vehicles: 10 | Hour: 8am")
print(f"Output → Congestion: {pred_congestion} | Signal: {pred_duration:.0f} seconds")