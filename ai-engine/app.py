
import json
import math
from pathlib import Path
import pandas as pd
import joblib
import numpy as np
import torch
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from torch import nn


BASE_DIR = Path(__file__).resolve().parent
ARTIFACTS = BASE_DIR / "artifacts"


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


class Autoencoder(nn.Module):
    def __init__(self, input_dim):
        super().__init__()
        self.network = nn.Sequential(
            nn.Linear(input_dim, 6),
            nn.ReLU(),
            nn.Linear(6, 3),
            nn.ReLU(),
            nn.Linear(3, 6),
            nn.ReLU(),
            nn.Linear(6, input_dim),
        )

    def forward(self, x):
        return self.network(x)


class RequestFeatures(BaseModel):
    path_length: float = Field(ge=0)
    query_length: float = Field(ge=0)
    query_param_count: float = Field(ge=0)
    header_count: float = Field(ge=0)
    user_agent_length: float = Field(ge=0)
    request_body_bytes: float = Field(ge=0)
    interarrival_ms: float = Field(ge=0)
    requests_last_10s: float = Field(ge=0)


app = FastAPI(title="AI API Security Service", version="0.1.0")

model = None
scaler = None
threshold = None


@app.on_event("startup")
def load_artifacts():
    global model, scaler, threshold

    with (ARTIFACTS / "metadata.json").open(
        encoding="utf-8"
    ) as file:
        metadata = json.load(file)

    if metadata["features"] != FEATURES:
        raise RuntimeError("Model feature order does not match API.")

    scaler = joblib.load(ARTIFACTS / "scaler.joblib")

    model = Autoencoder(len(FEATURES))
    state = torch.load(
        ARTIFACTS / "autoencoder.pt",
        map_location="cpu",
        weights_only=True,
    )
    model.load_state_dict(state)
    model.eval()

    threshold = float(metadata["threshold"])


@app.get("/health")
def health():
    return {
        "status": "healthy" if model is not None else "not_ready",
        "model_loaded": model is not None,
    }


@app.post("/score")
def score(features: RequestFeatures):
    values = features.model_dump()

    if not all(math.isfinite(v) for v in values.values()):
        raise HTTPException(
            status_code=422,
            detail="Features must be finite numbers.",
        )

    # Preserve the exact feature order used during training.
    raw = pd.DataFrame(
    [[values[name] for name in FEATURES]],
    columns=FEATURES,
    )

    normalized = scaler.transform(raw).astype(np.float32)
    tensor = torch.from_numpy(normalized)

    with torch.no_grad():
        reconstructed = model(tensor)
        error = torch.mean(
            (tensor - reconstructed) ** 2,
            dim=1,
        ).item()

    anomalous = error > threshold

    return {
        "anomaly_score": round(error, 6),
        "threshold": round(threshold, 6),
        "anomalous": anomalous,
        "decision": "BLOCK" if anomalous else "ALLOW",
        "model": "autoencoder-v1",
    }
