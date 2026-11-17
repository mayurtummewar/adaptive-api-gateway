import json
from pathlib import Path

import joblib
import pandas as pd
from sklearn.ensemble import RandomForestClassifier


ROOT = Path(__file__).resolve().parent.parent
DATASET = ROOT / "traffic-generator" / "traffic_dataset.csv"
ARTIFACTS = Path(__file__).resolve().parent / "artifacts"

FEATURES = [
    "path_length",
    "query_length",
    "query_param_count",
    "header_count",
    "user_agent_length",
    "request_body_bytes",
    "interarrival_ms",
    "requests_last_10s",
]


def main():
    df = pd.read_csv(DATASET)
    X = df[FEATURES]
    y = (df["label"] == "suspicious").astype(int)

    model = RandomForestClassifier(
        n_estimators=300,
        class_weight="balanced",
        min_samples_leaf=2,
        random_state=42,
    )
    model.fit(X, y)

    ARTIFACTS.mkdir(parents=True, exist_ok=True)
    joblib.dump(model, ARTIFACTS / "classifier.joblib")
    (ARTIFACTS / "classifier_metadata.json").write_text(
        json.dumps(
            {
                "model": "random-forest-v1",
                "features": FEATURES,
                "training_samples": len(df),
                "normal_samples": int((y == 0).sum()),
                "suspicious_samples": int((y == 1).sum()),
                "rate_limit_threshold": 0.5,
                "block_threshold": 0.9,
            },
            indent=2,
        ),
        encoding="utf-8",
    )

    print(f"Classifier trained on {len(df)} samples.")
    print(f"Artifacts saved to: {ARTIFACTS}")


if __name__ == "__main__":
    main()
