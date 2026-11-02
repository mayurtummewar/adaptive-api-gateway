
import joblib
import numpy as np
import pandas as pd
import torch
from pathlib import Path
from train import Autoencoder

ROOT = Path(__file__).resolve().parent
ARTIFACTS = ROOT / "artifacts"

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

metadata = __import__("json").loads(
    (ARTIFACTS / "metadata.json").read_text(encoding="utf-8")
)
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

request = pd.DataFrame([{
    "path_length": 6,
    "query_length": 12,
    "query_param_count": 1,
    "header_count": 4,
    "user_agent_length": 16,
    "request_body_bytes": 0,
    "interarrival_ms": 300,
    "requests_last_10s": 5,
}], columns=FEATURES)

scaled = scaler.transform(request).astype(np.float32)
tensor = torch.from_numpy(scaled)

with torch.no_grad():
    reconstructed = model(tensor).numpy()[0]

print("Feature-level reconstruction errors:")
for name, actual, predicted in zip(FEATURES, scaled[0], reconstructed):
    print(f"{name:24s} error={(actual - predicted) ** 2:.6f}")

print(f"\nThreshold: {metadata['threshold']:.6f}")
print(f"Total score: {np.mean((scaled[0] - reconstructed) ** 2):.6f}")
