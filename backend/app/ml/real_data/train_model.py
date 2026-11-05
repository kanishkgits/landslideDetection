"""Train a spatially grouped research classifier; outputs relative scores, not calibrated risk."""
import argparse, json
from pathlib import Path
import pandas as pd, numpy as np, joblib
from sklearn.ensemble import RandomForestClassifier, HistGradientBoostingClassifier
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline
from sklearn.model_selection import GroupShuffleSplit
from sklearn.metrics import average_precision_score, roc_auc_score, classification_report, confusion_matrix
from sklearn.calibration import calibration_curve

FEATURES=["rain_24h_mm","rain_72h_mm","rain_7d_mm",
          "soil_moisture_0_7cm_pct","soil_moisture_7_28cm_pct","elevation_m"]

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--csv",default="../data/processed/india_event_case_control.csv")
    p.add_argument("--out",default="app/ml/artifacts")
    args=p.parse_args()
    df=pd.read_csv(args.csv)
    required=FEATURES+["landslide_reported","pair_id"]
    missing=[c for c in required if c not in df.columns]
    if missing: raise ValueError(f"Missing columns: {missing}")
    df=df.dropna(subset=["landslide_reported","pair_id"])
    df["landslide_reported"]=df.landslide_reported.astype(int)
    if df.landslide_reported.nunique()!=2: raise ValueError("Both event and background classes required.")
    if df.pair_id.nunique()<20:
        raise ValueError(f"Only {df.pair_id.nunique()} matched event groups; need at least 20 for a minimal grouped evaluation.")
    X=df[FEATURES].replace([np.inf,-np.inf],np.nan); y=df.landslide_reported
    split=GroupShuffleSplit(n_splits=1,test_size=.25,random_state=42)
    tr,te=next(split.split(X,y,groups=df.pair_id))
    model=Pipeline([
      ("imputer",SimpleImputer(strategy="median",add_indicator=True)),
      ("rf",RandomForestClassifier(n_estimators=500,min_samples_leaf=2,
         class_weight="balanced_subsample",max_features="sqrt",random_state=42,n_jobs=-1))
    ])
    model.fit(X.iloc[tr],y.iloc[tr])
    pred=model.predict(X.iloc[te]); score=model.predict_proba(X.iloc[te])[:,1]
    metrics={
      "rows":int(len(df)),"event_pairs":int(df.pair_id.nunique()),
      "train_rows":int(len(tr)),"test_rows":int(len(te)),
      "average_precision":float(average_precision_score(y.iloc[te],score)),
      "roc_auc":float(roc_auc_score(y.iloc[te],score)),
      "classification_report":classification_report(y.iloc[te],pred,output_dict=True,zero_division=0),
      "confusion_matrix":confusion_matrix(y.iloc[te],pred).tolist(),
      "validation":"PAIR_GROUPED_RANDOM_HOLDOUT; NOT A SPATIAL OR TEMPORAL INDEPENDENT VALIDATION",
      "target":"NASA catalog reported event vs spatially displaced matched pseudo-absence",
      "interpretation":"Model score is a relative event-discrimination score, NOT calibrated landslide probability."
    }
    out=Path(args.out); out.mkdir(parents=True,exist_ok=True)
    joblib.dump({"model":model,"features":FEATURES,"target":metrics["target"],
                 "score_interpretation":metrics["interpretation"]},out/"terragaurd_event_model.joblib")
    (out/"metrics.json").write_text(json.dumps(metrics,indent=2))
    print(json.dumps(metrics,indent=2))
if __name__=="__main__": main()
