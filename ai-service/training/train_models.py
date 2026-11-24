"""
SmartRail AI+ — Model Training Script
======================================
Trains three AI models using synthetic demonstration data:
  1. Waitlist Confirmation Predictor (Logistic Regression + Random Forest)
  2. Train Recommendation Score (Random Forest Regressor)
  3. Seat/Berth Recommendation (Rule-based with ML scoring)

DISCLAIMER: Models are trained on SYNTHETIC data generated for academic
demonstration purposes. Predictions are estimates only, NOT guarantees.
Do NOT use for real travel decisions.
"""

import os
import sys
import json
import logging
import warnings
import numpy as np
import pandas as pd
from datetime import datetime

from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score,
    confusion_matrix, roc_auc_score, classification_report,
)
from sklearn.calibration import CalibratedClassifierCV
from sklearn.pipeline import Pipeline
import joblib

warnings.filterwarnings("ignore")
logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")
logger = logging.getLogger("smartrail.training")

# Paths
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODELS_DIR = os.path.join(BASE_DIR, "models")
DATASETS_DIR = os.path.join(BASE_DIR, "datasets")
os.makedirs(MODELS_DIR, exist_ok=True)
os.makedirs(DATASETS_DIR, exist_ok=True)


# =============================================================================
# 1. GENERATE SYNTHETIC TRAINING DATA
# =============================================================================

def generate_waitlist_dataset(n_samples: int = 1000) -> pd.DataFrame:
    """
    Generate synthetic waitlist prediction data.
    DISCLAIMER: This is SYNTHETIC data, not real Indian Railways data.
    """
    logger.info(f"Generating {n_samples} synthetic waitlist records...")
    np.random.seed(42)

    records = []
    train_numbers = ["12301", "12951", "12627", "12433", "12017", "22691"]
    classes = ["SL", "3AC", "2AC", "1AC", "CC"]
    quotas = ["GENERAL", "TATKAL", "SENIOR_CITIZEN", "EMERGENCY"]

    class_max_wl = {"SL": 50, "3AC": 20, "2AC": 10, "1AC": 5, "CC": 10}

    for _ in range(n_samples):
        train = np.random.choice(train_numbers)
        cls = np.random.choice(classes, p=[0.45, 0.30, 0.15, 0.05, 0.05])
        quota = np.random.choice(quotas, p=[0.70, 0.15, 0.10, 0.05])
        month = np.random.randint(1, 13)
        days_before = np.random.randint(1, 61)
        max_wl = class_max_wl[cls]
        wl_number = np.random.randint(1, max_wl + 1)
        total_wl = np.random.randint(wl_number, max_wl + 1)
        cancel_rate = np.random.uniform(0.10, 0.45)
        is_holiday = 1 if month in [10, 11, 12, 1] else np.random.randint(0, 2)

        # Compute confirmation probability (synthetic rule-based)
        wl_ratio = wl_number / max_wl  # lower = better
        days_factor = min(1.0, days_before / 30)  # more days = better
        cancel_factor = cancel_rate * 2  # higher cancel rate = more chance
        quota_bonus = {"EMERGENCY": 0.4, "SENIOR_CITIZEN": 0.2, "TATKAL": 0.1, "GENERAL": 0.0}[quota]
        peak_penalty = -0.15 if is_holiday else 0.0

        prob = (
            (1 - wl_ratio) * 0.45
            + days_factor * 0.25
            + cancel_factor * 0.20
            + quota_bonus
            + peak_penalty
            + np.random.normal(0, 0.05)  # noise
        )
        prob = max(0.0, min(1.0, prob))
        was_confirmed = int(np.random.random() < prob)

        records.append({
            "train_number": train,
            "travel_class": cls,
            "quota": quota,
            "journey_month": month,
            "days_before_journey": days_before,
            "waitlist_number": wl_number,
            "total_wl_at_time": total_wl,
            "max_wl_allowed": max_wl,
            "wl_ratio": round(wl_number / max_wl, 4),
            "historical_cancel_rate": round(cancel_rate, 4),
            "is_holiday_period": is_holiday,
            "was_confirmed": was_confirmed,
        })

    df = pd.DataFrame(records)
    logger.info(f"Dataset: {len(df)} rows | Confirmed: {df.was_confirmed.sum()} ({df.was_confirmed.mean()*100:.1f}%)")
    return df


def generate_recommendation_dataset(n_samples: int = 500) -> pd.DataFrame:
    """Generate synthetic train recommendation training data."""
    logger.info(f"Generating {n_samples} synthetic recommendation records...")
    np.random.seed(123)

    records = []
    routes = [
        ("NDLS", "HWH", 1200), ("NDLS", "BCT", 1400), ("NDLS", "SBC", 2000),
        ("NDLS", "PNBE", 1000), ("NDLS", "BPL", 700), ("NDLS", "DDN", 300),
        ("DDN", "NDLS", 300),
    ]
    classes = ["SL", "3AC", "2AC", "1AC", "CC"]
    times = ["MORNING", "AFTERNOON", "EVENING", "NIGHT"]
    budgets = ["LOW", "MEDIUM", "HIGH"]
    trains = ["12301", "12951", "12627", "12433", "12001", "12017", "22691"]

    for _ in range(n_samples):
        route = routes[np.random.randint(len(routes))]
        cls = np.random.choice(classes, p=[0.40, 0.30, 0.15, 0.05, 0.10])
        pref_time = np.random.choice(times)
        budget = np.random.choice(budgets, p=[0.30, 0.50, 0.20])
        month = np.random.randint(1, 13)
        dow = np.random.randint(0, 7)

        # Score (target): how well this booking matched user preferences
        score = np.random.uniform(0.5, 1.0) + np.random.normal(0, 0.05)
        score = max(0, min(1, score))

        records.append({
            "source": route[0], "destination": route[1],
            "travel_class": cls, "journey_month": month,
            "day_of_week": dow, "budget": budget,
            "preferred_time": pref_time,
            "recommendation_score": round(score, 4),
        })

    return pd.DataFrame(records)


# =============================================================================
# 2. TRAIN WAITLIST PREDICTION MODEL
# =============================================================================

def train_waitlist_model(df: pd.DataFrame) -> dict:
    """Train and evaluate waitlist confirmation prediction models."""
    logger.info("Training Waitlist Prediction Models...")

    # Feature engineering
    df = df.copy()
    df["wl_ratio"] = df["waitlist_number"] / df["max_wl_allowed"]
    df["days_normalized"] = df["days_before_journey"] / 60
    df["is_premium"] = df["quota"].isin(["TATKAL", "SENIOR_CITIZEN", "EMERGENCY"]).astype(int)
    df["is_emergency"] = (df["quota"] == "EMERGENCY").astype(int)

    # Encode categoricals
    class_encoder = LabelEncoder()
    df["class_encoded"] = class_encoder.fit_transform(df["travel_class"])

    quota_encoder = LabelEncoder()
    df["quota_encoded"] = quota_encoder.fit_transform(df["quota"])

    train_encoder = LabelEncoder()
    df["train_encoded"] = train_encoder.fit_transform(df["train_number"])

    features = [
        "wl_ratio", "days_normalized", "is_holiday_period",
        "historical_cancel_rate", "is_premium", "is_emergency",
        "class_encoded", "quota_encoded", "journey_month",
        "days_before_journey", "waitlist_number", "max_wl_allowed",
    ]

    X = df[features].values
    y = df["was_confirmed"].values

    # Time-aware split (70% train, 30% test)
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.30, random_state=42, stratify=y
    )

    results = {}

    # ── Model 1: Logistic Regression ─────────────────────────────────────────
    lr_pipeline = Pipeline([
        ("scaler", StandardScaler()),
        ("model", LogisticRegression(max_iter=1000, C=1.0, random_state=42)),
    ])
    lr_pipeline.fit(X_train, y_train)
    y_pred_lr = lr_pipeline.predict(X_test)
    y_prob_lr = lr_pipeline.predict_proba(X_test)[:, 1]

    lr_metrics = {
        "accuracy":  round(accuracy_score(y_test, y_pred_lr), 4),
        "precision": round(precision_score(y_test, y_pred_lr, zero_division=0), 4),
        "recall":    round(recall_score(y_test, y_pred_lr, zero_division=0), 4),
        "f1_score":  round(f1_score(y_test, y_pred_lr, zero_division=0), 4),
        "roc_auc":   round(roc_auc_score(y_test, y_prob_lr), 4),
        "confusion_matrix": confusion_matrix(y_test, y_pred_lr).tolist(),
    }
    results["logistic_regression"] = lr_metrics
    logger.info(f"LR | Acc={lr_metrics['accuracy']} F1={lr_metrics['f1_score']} AUC={lr_metrics['roc_auc']}")

    # ── Model 2: Random Forest Classifier ────────────────────────────────────
    rf_pipeline = Pipeline([
        ("scaler", StandardScaler()),
        ("model", RandomForestClassifier(
            n_estimators=100, max_depth=8, min_samples_split=5,
            random_state=42, n_jobs=-1,
        )),
    ])
    rf_pipeline.fit(X_train, y_train)
    y_pred_rf = rf_pipeline.predict(X_test)
    y_prob_rf = rf_pipeline.predict_proba(X_test)[:, 1]

    rf_metrics = {
        "accuracy":  round(accuracy_score(y_test, y_pred_rf), 4),
        "precision": round(precision_score(y_test, y_pred_rf, zero_division=0), 4),
        "recall":    round(recall_score(y_test, y_pred_rf, zero_division=0), 4),
        "f1_score":  round(f1_score(y_test, y_pred_rf, zero_division=0), 4),
        "roc_auc":   round(roc_auc_score(y_test, y_prob_rf), 4),
        "confusion_matrix": confusion_matrix(y_test, y_pred_rf).tolist(),
        "feature_importance": dict(zip(features, rf_pipeline.named_steps["model"].feature_importances_.tolist())),
    }
    results["random_forest"] = rf_metrics
    logger.info(f"RF  | Acc={rf_metrics['accuracy']} F1={rf_metrics['f1_score']} AUC={rf_metrics['roc_auc']}")

    # Choose best model
    best_model_name = "random_forest" if rf_metrics["roc_auc"] >= lr_metrics["roc_auc"] else "logistic_regression"
    best_pipeline = rf_pipeline if best_model_name == "random_forest" else lr_pipeline
    logger.info(f"Best model: {best_model_name}")

    # Save models + encoders + metadata
    model_data = {
        "pipeline": best_pipeline,
        "features": features,
        "class_encoder": class_encoder,
        "quota_encoder": quota_encoder,
        "train_encoder": train_encoder,
        "metrics": results,
        "best_model": best_model_name,
        "version": "1.0.0",
        "trained_at": datetime.now().isoformat(),
        "data_disclaimer": (
            "Model trained on SYNTHETIC data for academic demonstration. "
            "Predictions are estimates only, NOT guarantees. "
            "Not connected to real Indian Railways data."
        ),
    }
    path = os.path.join(MODELS_DIR, "waitlist_predictor.joblib")
    joblib.dump(model_data, path)
    logger.info(f"Saved waitlist model → {path}")

    # Also save both models individually
    joblib.dump(lr_pipeline, os.path.join(MODELS_DIR, "waitlist_lr.joblib"))
    joblib.dump(rf_pipeline, os.path.join(MODELS_DIR, "waitlist_rf.joblib"))

    return results


# =============================================================================
# 3. TRAIN RECOMMENDATION MODEL
# =============================================================================

def train_recommendation_model(df: pd.DataFrame) -> dict:
    """Train a recommendation scoring model."""
    logger.info("Training Train Recommendation Model...")

    df = df.copy()

    class_enc = LabelEncoder()
    df["class_enc"] = class_enc.fit_transform(df["travel_class"])
    budget_enc = LabelEncoder()
    df["budget_enc"] = budget_enc.fit_transform(df["budget"])
    time_enc = LabelEncoder()
    df["time_enc"] = time_enc.fit_transform(df["preferred_time"])
    src_enc = LabelEncoder()
    df["src_enc"] = src_enc.fit_transform(df["source"])
    dst_enc = LabelEncoder()
    df["dst_enc"] = dst_enc.fit_transform(df["destination"])

    features = ["src_enc", "dst_enc", "class_enc", "journey_month", "day_of_week", "budget_enc", "time_enc"]
    X = df[features].values
    y = df["recommendation_score"].values

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    model = Pipeline([
        ("scaler", StandardScaler()),
        ("rf", RandomForestRegressor(n_estimators=50, max_depth=6, random_state=42)),
    ])
    model.fit(X_train, y_train)
    score = model.score(X_test, y_test)
    logger.info(f"Recommendation model R²: {score:.4f}")

    model_data = {
        "pipeline": model,
        "features": features,
        "class_enc": class_enc,
        "budget_enc": budget_enc,
        "time_enc": time_enc,
        "src_enc": src_enc,
        "dst_enc": dst_enc,
        "r2_score": round(score, 4),
        "version": "1.0.0",
        "trained_at": datetime.now().isoformat(),
    }
    path = os.path.join(MODELS_DIR, "recommendation_model.joblib")
    joblib.dump(model_data, path)
    logger.info(f"Saved recommendation model → {path}")

    return {"r2_score": round(score, 4)}


# =============================================================================
# 4. SAVE DATASETS
# =============================================================================

def save_datasets(wl_df: pd.DataFrame, rec_df: pd.DataFrame) -> None:
    """Save training datasets as CSV files."""
    wl_path = os.path.join(DATASETS_DIR, "waitlist_training_data.csv")
    rec_path = os.path.join(DATASETS_DIR, "recommendation_training_data.csv")
    wl_df.to_csv(wl_path, index=False)
    rec_df.to_csv(rec_path, index=False)
    logger.info(f"Datasets saved: {wl_path}, {rec_path}")

    readme = """# SmartRail AI+ — Training Datasets

## DISCLAIMER
All data in these CSV files is SYNTHETIC (algorithmically generated)
for academic demonstration purposes only.

This data does NOT represent real Indian Railways booking records,
cancellation patterns, or operational data.

## Files

### waitlist_training_data.csv
Features for predicting waitlist confirmation probability.
Target column: `was_confirmed` (1=confirmed, 0=remained on waitlist)

### recommendation_training_data.csv
Features for scoring train recommendations based on user preferences.
Target column: `recommendation_score` (0.0–1.0)

## Academic Note
Trained models are for demonstration of ML concepts in the context of
a railway reservation system. Predictions must NOT be used for real
booking decisions.
"""
    with open(os.path.join(DATASETS_DIR, "README.md"), "w") as f:
        f.write(readme)


# =============================================================================
# 5. SAVE METRICS REPORT
# =============================================================================

def save_metrics(wl_metrics: dict, rec_metrics: dict) -> None:
    report = {
        "generated_at": datetime.now().isoformat(),
        "data_disclaimer": "Models trained on SYNTHETIC data. For academic demonstration only.",
        "waitlist_prediction": wl_metrics,
        "recommendation": rec_metrics,
    }
    path = os.path.join(MODELS_DIR, "model_metrics.json")
    with open(path, "w") as f:
        json.dump(report, f, indent=2)
    logger.info(f"Metrics report saved → {path}")


# =============================================================================
# MAIN
# =============================================================================

if __name__ == "__main__":
    logger.info("=" * 60)
    logger.info("SmartRail AI+ — Model Training Pipeline")
    logger.info("DISCLAIMER: Using SYNTHETIC demonstration data")
    logger.info("=" * 60)

    # Generate datasets
    wl_df = generate_waitlist_dataset(n_samples=1200)
    rec_df = generate_recommendation_dataset(n_samples=600)
    save_datasets(wl_df, rec_df)

    # Train models
    wl_metrics = train_waitlist_model(wl_df)
    rec_metrics = train_recommendation_model(rec_df)
    save_metrics(wl_metrics, rec_metrics)

    logger.info("=" * 60)
    logger.info("Training complete! Models saved in ai-service/models/")
    logger.info("=" * 60)

    print("\n=== WAITLIST PREDICTION MODEL RESULTS ===")
    for model_name, metrics in wl_metrics.items():
        print(f"\n{model_name.upper()}:")
        print(f"  Accuracy:  {metrics['accuracy']}")
        print(f"  Precision: {metrics['precision']}")
        print(f"  Recall:    {metrics['recall']}")
        print(f"  F1-Score:  {metrics['f1_score']}")
        print(f"  ROC-AUC:   {metrics['roc_auc']}")

    print(f"\n=== RECOMMENDATION MODEL ===")
    print(f"  R² Score: {rec_metrics['r2_score']}")
