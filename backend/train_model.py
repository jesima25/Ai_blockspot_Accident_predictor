# train_model.py
# Purpose: Load dataset, train AI model, save model

import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import accuracy_score, classification_report
from sklearn.utils import resample
import joblib

print("=" * 50)
print("   AI BLACKSPOT DETECTION - MODEL TRAINING")
print("=" * 50)

# ─────────────────────────────────────────
# STEP 1 — LOAD DATASET
# ─────────────────────────────────────────
print("\n[1] Loading dataset...")

df = pd.read_csv("accident_data.csv")
print(f"    Dataset loaded: {df.shape[0]} rows, {df.shape[1]} columns")

# ─────────────────────────────────────────
# STEP 2 — SELECT AND FILL COLUMNS
# ─────────────────────────────────────────
print("\n[2] Cleaning data...")

useful_columns = [
    'weather',
    'road_type',
    'hour',
    'is_weekend',
    'traffic_density',
    'visibility',
    'is_peak_hour',
    'risk_score',
    'accident_severity'
]

available = [col for col in useful_columns if col in df.columns]
df = df[available].copy()

# Fill missing values
df['weather']           = df['weather'].fillna('clear')
df['road_type']         = df['road_type'].fillna('urban')
df['traffic_density']   = df['traffic_density'].fillna('medium')
df['visibility']        = df['visibility'].fillna('medium')
df['is_peak_hour']      = df['is_peak_hour'].fillna(0)
df['is_weekend']        = df['is_weekend'].fillna(0)
df['hour']              = df['hour'].fillna(12)
df['risk_score']        = df['risk_score'].fillna(0.5)
df['accident_severity'] = df['accident_severity'].fillna('minor')

print(f"    Using columns: {available}")
print(f"    Dataset size : {df.shape[0]} rows")

# ─────────────────────────────────────────
# STEP 3 — ENCODE TEXT COLUMNS
# ─────────────────────────────────────────
print("\n[3] Encoding text columns...")

encoders = {}
text_columns = ['weather', 'road_type', 'traffic_density',
                'visibility', 'accident_severity']

for col in text_columns:
    if col in df.columns:
        le = LabelEncoder()
        df[col] = le.fit_transform(df[col].astype(str))
        encoders[col] = le
        print(f"    Encoded: {col} → {list(le.classes_)}")

# Convert all to numeric
for col in df.columns:
    df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)

# ─────────────────────────────────────────
# STEP 4 — FIX IMBALANCED DATASET
# ─────────────────────────────────────────
print("\n[4] Balancing dataset...")

print(f"    Before balancing:")
counts = df['accident_severity'].value_counts()
labels = encoders['accident_severity'].classes_
for i, label in enumerate(labels):
    print(f"       {label}: {counts.get(i, 0)} rows")

# Separate by class
df_fatal = df[df['accident_severity'] == 0]
df_major = df[df['accident_severity'] == 1]
df_minor = df[df['accident_severity'] == 2]

target_size = 5000

# Upsample minority classes
df_fatal_up = resample(df_fatal, replace=True,
                       n_samples=target_size, random_state=42)
df_major_up = resample(df_major, replace=True,
                       n_samples=target_size, random_state=42)
df_minor_up = resample(df_minor, replace=False,
                       n_samples=target_size, random_state=42)

df_balanced = pd.concat([df_fatal_up, df_major_up, df_minor_up])
df_balanced = df_balanced.sample(frac=1, random_state=42).reset_index(drop=True)

print(f"\n    After balancing:")
print(f"       fatal : {target_size} rows")
print(f"       major : {target_size} rows")
print(f"       minor : {target_size} rows")
print(f"       Total : {df_balanced.shape[0]} rows")

# ─────────────────────────────────────────
# STEP 5 — SPLIT FEATURES AND TARGET
# ─────────────────────────────────────────
print("\n[5] Splitting features and target...")

X = df_balanced.drop('accident_severity', axis=1)
y = df_balanced['accident_severity']

print(f"    Features : {list(X.columns)}")

# ─────────────────────────────────────────
# STEP 6 — TRAIN TEST SPLIT
# ─────────────────────────────────────────
print("\n[6] Train/Test split...")

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42, stratify=y
)

print(f"    Training size : {X_train.shape[0]} rows")
print(f"    Testing size  : {X_test.shape[0]} rows")

# ─────────────────────────────────────────
# STEP 7 — TRAIN MODEL
# ─────────────────────────────────────────
print("\n[7] Training Random Forest model...")

model = RandomForestClassifier(
    n_estimators=300,
    max_depth=20,
    min_samples_split=3,
    min_samples_leaf=1,
    class_weight='balanced',
    random_state=42,
    n_jobs=-1
)

model.fit(X_train, y_train)
print("    Model trained successfully!")

# ─────────────────────────────────────────
# STEP 8 — EVALUATE MODEL
# ─────────────────────────────────────────
print("\n[8] Evaluating model...")

y_pred = model.predict(X_test)
accuracy = accuracy_score(y_test, y_pred)

print(f"\n    Accuracy: {accuracy * 100:.2f}%")
print("\n    Classification Report:")
print(classification_report(
    y_test, y_pred,
    target_names=encoders['accident_severity'].classes_
))

# ─────────────────────────────────────────
# STEP 9 — SAVE MODEL
# ─────────────────────────────────────────
print("\n[9] Saving model...")

joblib.dump(model,           "model.pkl")
joblib.dump(list(X.columns), "feature_columns.pkl")
joblib.dump(encoders,        "encoders.pkl")

print("    model.pkl            saved")
print("    feature_columns.pkl  saved")
print("    encoders.pkl         saved")

# ─────────────────────────────────────────
# STEP 10 — FEATURE IMPORTANCE
# ─────────────────────────────────────────
print("\n[10] Feature Importance:")

for name, score in sorted(
    zip(X.columns, model.feature_importances_),
    key=lambda x: x[1], reverse=True
):
    bar = "█" * int(score * 50)
    print(f"    {name:<25} {bar} {score:.4f}")

print("\n" + "=" * 50)
print("   TRAINING COMPLETE!")
print("   Now run: python app.py")
print("=" * 50)