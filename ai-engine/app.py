import json
import math
from pathlib import Path

import joblib
import pandas as pd
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field


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


class RequestFeatures(BaseModel):
    path_length: float = Field(ge=0)
    query_length: float = Field(ge=0)
    query_param_count: float = Field(ge=0)
    header_count: float = Field(ge=0)
    user_agent_length: float = Field(ge=0)
    request_body_bytes: float = Field(ge=0)
    interarrival_ms: float = Field(ge=0)
    requests_last_10s: float = Field(ge=0)


app = FastAPI(title="AI API Security Service", version="0.2.0")

model = None
rate_limit_threshold = None
block_threshold = None


@app.on_event("startup")
def load_artifacts():
    global model, rate_limit_threshold, block_threshold

    with (ARTIFACTS / "classifier_metadata.json").open(
        encoding="utf-8"
    ) as file:
        metadata = json.load(file)

    if metadata["features"] != FEATURES:
        raise RuntimeError("Model feature order does not match API.")

    model = joblib.load(ARTIFACTS / "classifier.joblib")
    rate_limit_threshold = float(metadata["rate_limit_threshold"])
    block_threshold = float(metadata["block_threshold"])


@app.get("/health")
def health():
    return {
        "status": "healthy" if model is not None else "not_ready",
        "model_loaded": model is not None,
        "model": "random-forest-v1",
    }


@app.post("/score")
def score(features: RequestFeatures):
    values = features.model_dump()

    if not all(math.isfinite(value) for value in values.values()):
        raise HTTPException(
            status_code=422,
            detail="Features must be finite numbers.",
        )

    ordered_values = pd.DataFrame(
        [[values[name] for name in FEATURES]],
        columns=FEATURES,
    )
    suspicious_probability = float(model.predict_proba(ordered_values)[0][1])

    if suspicious_probability >= block_threshold:
        decision = "BLOCK"
    elif suspicious_probability >= rate_limit_threshold:
        decision = "RATE LIMIT"
    else:
        decision = "ALLOW"

    return {
        "anomaly_score": round(suspicious_probability, 6),
        "suspicious_probability": round(suspicious_probability, 6),
        "rate_limit_threshold": rate_limit_threshold,
        "block_threshold": block_threshold,
        "anomalous": decision != "ALLOW",
        "decision": decision,
        "model": "random-forest-v1",
    }
