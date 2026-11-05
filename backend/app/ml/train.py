import argparse, json
from pathlib import Path
import pandas as pd
import joblib
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, average_precision_score, roc_auc_score
from sklearn.pipeline import Pipeline
from sklearn.impute import SimpleImputer

FEATURES = ["rain_1h_mm", "rain_24h_mm", "rain_72h_mm", "rain_7d_mm",
            "slope_deg", "elevation_m", "soil_moisture_pct"]

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--csv", required=True)
    parser.add_argument("--out", default="app/ml/artifacts")
    args = parser.parse_args()
    df = pd.read_csv(args.csv)
    missing = [c for c in FEATURES + ["landslide"] if c not in df.columns]
    if missing: raise ValueError(f"Missing required columns: {missing}")
    df = df[FEATURES + ["landslide"]].dropna(subset=["landslide"])
    if set(df.landslide.unique()) - {0, 1}: raise ValueError("landslide target must be binary 0/1")
    if df.landslide.nunique() != 2: raise ValueError("Training requires both classes.")
    X, y = df[FEATURES], df["landslide"].astype(int)
    Xtr, Xte, ytr, yte = train_test_split(X, y, test_size=.2, random_state=42, stratify=y)
    model = Pipeline([("imputer", SimpleImputer(strategy="median")),
                      ("rf", RandomForestClassifier(n_estimators=400, min_samples_leaf=2,
                       class_weight="balanced", random_state=42, n_jobs=-1))])
    model.fit(Xtr, ytr)
    pred = model.predict(Xte)
    prob = model.predict_proba(Xte)[:, 1]
    report = classification_report(yte, pred, output_dict=True, zero_division=0)
    metrics = {"n_rows": len(df), "positive_rate": float(y.mean()),
               "average_precision": float(average_precision_score(yte, prob)),
               "roc_auc": float(roc_auc_score(yte, prob)),
               "classification_report": report,
               "validation": "STRATIFIED_RANDOM_BASELINE_ONLY_NOT_SPATIAL_OR_TEMPORAL"}
    out = Path(args.out); out.mkdir(parents=True, exist_ok=True)
    joblib.dump({"model": model, "features": FEATURES}, out / "landslide_model.joblib")
    (out / "metrics.json").write_text(json.dumps(metrics, indent=2))
    print(json.dumps(metrics, indent=2))
if __name__ == "__main__": main()
