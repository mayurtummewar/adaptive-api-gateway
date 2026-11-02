
import json
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
import torch
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from torch import nn

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


def reconstruction_errors(model, data):
    tensor = torch.from_numpy(data.astype(np.float32))

    with torch.no_grad():
        reconstructed = model(tensor)
        errors = ((tensor - reconstructed) ** 2).mean(dim=1)

    return errors.numpy()


def main():
    df = pd.read_csv(DATASET)
    normal = df.loc[df["label"] == "normal", FEATURES].copy()

    # Keep calibration data separate from model training.
    train_df, calibration_df = train_test_split(
        normal,
        test_size=0.25,
        random_state=42,
    )

    scaler = StandardScaler()
    X_train = scaler.fit_transform(train_df).astype(np.float32)
    X_calibration = scaler.transform(calibration_df).astype(np.float32)

    torch.manual_seed(42)
    model = Autoencoder(len(FEATURES))
    optimizer = torch.optim.Adam(model.parameters(), lr=0.005)
    loss_fn = nn.MSELoss()
    X_tensor = torch.from_numpy(X_train)

    model.train()

    for epoch in range(200):
        optimizer.zero_grad()
        reconstructed = model(X_tensor)
        loss = loss_fn(reconstructed, X_tensor)
        loss.backward()
        optimizer.step()

        if (epoch + 1) % 50 == 0:
            print(f"Epoch {epoch + 1}/200 | Loss: {loss.item():.6f}")

    model.eval()

    calibration_errors = reconstruction_errors(
        model, X_calibration
    )

    # Empirical calibration threshold; a small calibration set
    # cannot provide a precise estimate of the 95th percentile.
    threshold = float(np.percentile(calibration_errors, 95))

    ARTIFACTS.mkdir(parents=True, exist_ok=True)

    torch.save(model.state_dict(), ARTIFACTS / "autoencoder.pt")
    joblib.dump(scaler, ARTIFACTS / "scaler.joblib")

    metadata = {
        "features": FEATURES,
        "threshold": threshold,
        "training_samples": len(train_df),
        "calibration_samples": len(calibration_df),
        "calibration_percentile": 95,
        "training_loss": float(loss.item()),
    }

    (ARTIFACTS / "metadata.json").write_text(
        json.dumps(metadata, indent=2),
        encoding="utf-8",
    )

    print("\nTraining complete.")
    print(f"Training samples: {len(train_df)}")
    print(f"Calibration samples: {len(calibration_df)}")
    print(f"Calibration threshold: {threshold:.6f}")
    print(f"Artifacts saved to: {ARTIFACTS}")


if __name__ == "__main__":
    main()
