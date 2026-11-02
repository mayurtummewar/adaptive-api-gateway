
import json
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
import torch

from train import Autoencoder, FEATURES

ROOT = Path(__file__).resolve().parent.parent
ARTIFACTS = Path(__file__).resolve().parent / "artifacts"
DATASET = ROOT / "traffic-generator" / "traffic_dataset.csv"

metadata = json.loads(
    (ARTIFACTS / "metadata.json").read_text(encoding="utf-8")
)

df = pd.read_csv(DATASET)
scaler = joblib.load(ARTIFACTS / "scaler.joblib")

model = Autoencoder(len(FEATURES))
model.load_state_dict(
    torch.load(
        ARTIFACTS / "autoencoder.pt",
        map_location="cpu",
        weights_only=True,
    )
)
model.eval()

X = scaler.transform(df[FEATURES]).astype(np.float32)
tensor = torch.from_numpy(X)

with torch.no_grad():
    reconstructed = model(tensor)
    errors = ((tensor - reconstructed) ** 2).mean(dim=1).numpy()

df["anomaly_score"] = errors
threshold = metadata["threshold"]
df["predicted_anomaly"] = df["anomaly_score"] > threshold

print("\nScore summary by actual label:")
print(
    df.groupby("label")["anomaly_score"]
    .agg(["count", "min", "median", "max", "mean"])
    .round(4)
)

print(f"\nSaved threshold: {threshold:.6f}")
print("\nNormal records incorrectly flagged:")
print(
    df[df["label"] == "normal"][
        ["query_length", "interarrival_ms",
         "requests_last_10s", "anomaly_score"]
    ]
    .sort_values("anomaly_score", ascending=False)
    .head(10)
    .to_string(index=False)
)

print("\nDetection counts:")
print(pd.crosstab(
    df["label"],
    df["predicted_anomaly"],
    rownames=["Actual label"],
    colnames=["Predicted anomaly"],
))
