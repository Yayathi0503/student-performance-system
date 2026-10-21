"""Evaluate the trusted trained model against its saved held-out test data."""
import json
from pathlib import Path

import pandas as pd

from app.services.prediction import FEATURES, load_model
from ml.train_model import metrics

if __name__ == "__main__":
    artifact = load_model(Path("artifacts/model.joblib"))
    if artifact is None:
        raise SystemExit("Run python -m ml.train_model first")
    data = pd.read_csv("artifacts/test_data.csv")
    print(json.dumps(metrics(data.needs_support, artifact["model"].predict(data[FEATURES])), indent=2))
