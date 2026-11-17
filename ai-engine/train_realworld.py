import json
import math
import random
import re
from collections import deque
from pathlib import Path
from urllib.parse import parse_qsl, urlsplit

import joblib
import numpy as np
import pandas as pd
import torch
from sklearn.metrics import classification_report, confusion_matrix, roc_auc_score
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from torch import nn
from torch.utils.data import DataLoader, TensorDataset


ROOT = Path(__file__).resolve().parent.parent
DATASETS = ROOT / "datasets"
CSIC_DATASET = (
    DATASETS / "Web-Application-Attack-Datasets" / "CSVData" / "csic_final.csv"
)
ECLOG_DATASET = DATASETS / "eclog" / "1day" / "eclog_1day.csv"
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
    "text_length",
    "special_char_count",
    "percent_encoded_count",
    "sql_keyword_count",
    "xss_keyword_count",
    "traversal_count",
    "shell_metachar_count",
    "path_depth",
    "digit_ratio",
]
LOG_FEATURES = [
    "query_length",
    "user_agent_length",
    "request_body_bytes",
    "interarrival_ms",
    "requests_last_10s",
    "text_length",
    "special_char_count",
    "percent_encoded_count",
    "sql_keyword_count",
    "xss_keyword_count",
    "traversal_count",
    "shell_metachar_count",
    "path_depth",
]


class TrafficClassifier(nn.Module):
    def __init__(self):
        super().__init__()
        self.network = nn.Sequential(
            nn.Linear(len(FEATURES), 32),
            nn.ReLU(),
            nn.Dropout(0.15),
            nn.Linear(32, 16),
            nn.ReLU(),
            nn.Linear(16, 1),
        )

    def forward(self, values):
        return self.network(values).squeeze(1)


def query_parts(uri: str, query: str) -> tuple[int, int]:
    parsed = urlsplit(uri or "")
    raw_query = query or parsed.query
    if not raw_query:
        return 0, 0
    return len(raw_query), len(parse_qsl(raw_query, keep_blank_values=True))


def request_features(
    *,
    uri: str,
    query: str = "",
    body: str = "",
    method: str = "",
    header_count: int = 0,
    user_agent: str = "",
    interarrival_ms: float = 0.0,
    requests_last_10s: int = 1,
) -> list[float]:
    parsed = urlsplit(uri or "")
    query_length, query_param_count = query_parts(uri, query)
    text = " ".join((uri or "", query or "", body or "")).lower()
    text_length = len(text)
    special_char_count = sum(not character.isalnum() for character in text)
    percent_encoded_count = len(re.findall(r"%[0-9a-f]{2}", text))
    sql_keyword_count = len(
        re.findall(r"\b(?:select|union|insert|update|delete|drop|where)\b", text)
    )
    xss_keyword_count = len(
        re.findall(r"(?:<script|javascript:|onerror\s*=|onload\s*=|alert\s*\()", text)
    )
    traversal_count = len(re.findall(r"(?:\.\./|\.\.\\|%2e)", text))
    shell_metachar_count = sum(text.count(token) for token in (";", "|", "&&", "`"))
    alphanumeric_count = sum(character.isalnum() for character in text)
    return [
        float(len(parsed.path)),
        float(query_length),
        float(query_param_count),
        float(header_count),
        float(len(user_agent or "")),
        float(len(body or "")),
        float(interarrival_ms),
        float(requests_last_10s),
        float(text_length),
        float(special_char_count),
        float(percent_encoded_count),
        float(sql_keyword_count),
        float(xss_keyword_count),
        float(traversal_count),
        float(shell_metachar_count),
        float(parsed.path.count("/")),
        float(sum(character.isdigit() for character in text) / max(alphanumeric_count, 1)),
    ]


def load_csic() -> tuple[pd.DataFrame, np.ndarray]:
    df = pd.read_csv(CSIC_DATASET).fillna("")
    request_key = (
        df["Class"].astype(str)
        + "\x1f"
        + df["Method"].astype(str)
        + "\x1f"
        + df["URI"].astype(str)
        + "\x1f"
        + df["POST-Data"].astype(str)
        + "\x1f"
        + df["GET-Query"].astype(str)
    )
    df = df.assign(_request_key=request_key).drop_duplicates("_request_key")

    header_columns = [
        "Host-Header",
        "Host",
        "Connection",
        "Accept",
        "Accept-Charset",
        "Accept-Language",
        "Cache-control",
        "Cookie",
        "Pragma",
        "Content-Type",
    ]
    features = [
        request_features(
            uri=row["URI"],
            query=row["GET-Query"],
            body=row["POST-Data"],
            method=row["Method"],
            header_count=sum(bool(row[column]) for column in header_columns),
            user_agent=row["User-Agent"],
        )
        for _, row in df.iterrows()
    ]
    labels = (df["Class"] == "Anomalous").astype(np.float32).to_numpy()
    return pd.DataFrame(features, columns=FEATURES), labels


def load_eclog() -> pd.DataFrame:
    df = pd.read_csv(ECLOG_DATASET).fillna("")
    timestamps = pd.to_numeric(df["TimeStamp"])
    interarrival = timestamps.diff().fillna(0).clip(lower=0) / 10000
    recent_timestamps: deque[int] = deque()
    request_counts = []
    for timestamp in timestamps:
        recent_timestamps.append(int(timestamp))
        while recent_timestamps[0] < timestamp - 100_000_000:
            recent_timestamps.popleft()
        request_counts.append(len(recent_timestamps))
    features = [
        request_features(
            uri=row["Uri"],
            method=row["HttpMethod"],
            header_count=3,
            user_agent=row["UserAgent"],
            interarrival_ms=interarrival.iloc[index],
            requests_last_10s=request_counts[index],
        )
        for index, (_, row) in enumerate(df.iterrows())
    ]
    return pd.DataFrame(features, columns=FEATURES)


def probabilities(model, values: np.ndarray, device: torch.device) -> np.ndarray:
    model.eval()
    with torch.no_grad():
        tensor = torch.from_numpy(values).to(device)
        return torch.sigmoid(model(tensor)).cpu().numpy()


def main():
    random.seed(42)
    np.random.seed(42)
    torch.manual_seed(42)

    csic_features, csic_labels = load_csic()
    csic_train, csic_test, csic_train_labels, csic_test_labels = train_test_split(
        csic_features,
        csic_labels,
        test_size=0.2,
        stratify=csic_labels,
        random_state=42,
    )
    csic_train, csic_validation, csic_train_labels, csic_validation_labels = (
        train_test_split(
            csic_train,
            csic_train_labels,
            test_size=0.2,
            stratify=csic_train_labels,
            random_state=42,
        )
    )
    eclog = load_eclog()
    eclog_train_end = int(len(eclog) * 0.7)
    eclog_validation_end = int(len(eclog) * 0.85)
    eclog_train = eclog.iloc[:eclog_train_end].sample(
        n=min(25_000, eclog_train_end),
        random_state=42,
    )
    eclog_validation = eclog.iloc[eclog_train_end:eclog_validation_end].sample(
        n=min(10_000, eclog_validation_end - eclog_train_end),
        random_state=42,
    )
    eclog_test = eclog.iloc[eclog_validation_end:]

    train_features = pd.concat([csic_train, eclog_train], ignore_index=True)
    train_labels = np.concatenate(
        [csic_train_labels, np.zeros(len(eclog_train), dtype=np.float32)]
    )
    validation_features = pd.concat(
        [csic_validation, eclog_validation],
        ignore_index=True,
    )
    validation_labels = np.concatenate(
        [
            csic_validation_labels,
            np.zeros(len(eclog_validation), dtype=np.float32),
        ]
    )
    test_features = csic_test
    test_labels = csic_test_labels

    for frame in (train_features, validation_features, test_features, eclog_test):
        frame[LOG_FEATURES] = np.log1p(frame[LOG_FEATURES])

    scaler = StandardScaler()
    train_values = scaler.fit_transform(train_features).astype(np.float32)
    validation_values = scaler.transform(validation_features).astype(np.float32)
    test_values = scaler.transform(test_features).astype(np.float32)

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model = TrafficClassifier().to(device)
    dataset = TensorDataset(
        torch.from_numpy(train_values),
        torch.from_numpy(train_labels),
    )
    loader = DataLoader(dataset, batch_size=256, shuffle=True)
    positive_weight = torch.tensor(
        [(train_labels == 0).sum() / (train_labels == 1).sum()],
        device=device,
    )
    loss_fn = nn.BCEWithLogitsLoss(pos_weight=positive_weight)
    optimizer = torch.optim.AdamW(model.parameters(), lr=0.001, weight_decay=0.0001)

    best_state = None
    best_validation_loss = math.inf
    patience = 0
    for epoch in range(100):
        model.train()
        for batch_values, batch_labels in loader:
            optimizer.zero_grad()
            loss = loss_fn(model(batch_values.to(device)), batch_labels.to(device))
            loss.backward()
            optimizer.step()

        model.eval()
        with torch.no_grad():
            validation_loss = loss_fn(
                model(torch.from_numpy(validation_values).to(device)),
                torch.from_numpy(validation_labels).to(device),
            ).item()
        if validation_loss < best_validation_loss:
            best_validation_loss = validation_loss
            best_state = {
                name: value.detach().cpu().clone()
                for name, value in model.state_dict().items()
            }
            patience = 0
        else:
            patience += 1
            if patience >= 12:
                break

    if best_state is None:
        raise RuntimeError("Training did not produce a validation checkpoint.")
    model.load_state_dict(best_state)

    test_probabilities = probabilities(model, test_values, device)
    test_predictions = (test_probabilities >= 0.5).astype(np.int32)
    print(f"device: {device}")
    print(f"deduplicated CSIC rows: {len(csic_features)}")
    print("CSIC test confusion matrix:")
    print(confusion_matrix(test_labels, test_predictions))
    print(classification_report(test_labels, test_predictions, zero_division=0))
    print(f"CSIC test ROC-AUC: {roc_auc_score(test_labels, test_probabilities):.4f}")

    eclog_values = scaler.transform(eclog_test).astype(np.float32)
    eclog_probabilities = probabilities(model, eclog_values, device)
    print(f"EClog normal holdout rows: {len(eclog_test)}")
    print(
        "EClog false-positive rate at 0.5: "
        f"{(eclog_probabilities >= 0.5).mean():.4%}"
    )
    print(
        "EClog probability quantiles: "
        f"{np.quantile(eclog_probabilities, [0.5, 0.95, 0.99]).round(4)}"
    )

    ARTIFACTS.mkdir(parents=True, exist_ok=True)
    torch.save(model.state_dict(), ARTIFACTS / "realworld_classifier.pt")
    joblib.dump(scaler, ARTIFACTS / "realworld_scaler.joblib")
    (ARTIFACTS / "realworld_metadata.json").write_text(
        json.dumps(
            {
                "model": "traffic-mlp-v1",
                "features": FEATURES,
                "device_used": str(device),
                "training_rows": len(train_features),
                "validation_rows": len(validation_features),
                "test_rows": len(test_features),
                "deduplicated_csic_rows": len(csic_features),
                "eclog_train_rows": len(eclog_train),
                "eclog_validation_rows": len(eclog_validation),
                "eclog_test_rows": len(eclog_test),
                "decision_threshold": 0.5,
                "log_features": LOG_FEATURES,
            },
            indent=2,
        ),
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
