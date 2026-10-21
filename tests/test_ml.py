import json

import numpy as np

from app.services.prediction import load_model, predict
from ml.train_model import synthetic_data


def test_reproducible_dataset():
    assert synthetic_data().equals(synthetic_data())
    assert set(synthetic_data().needs_support) == {0, 1}


def test_saved_model_and_metrics(model_dir):
    report = json.loads((model_dir / "metrics.json").read_text())
    assert set(report["models"]) == {"logistic_regression", "random_forest"}
    for model in report["models"].values():
        for split in ("validation", "test"):
            for metric in ("accuracy", "precision", "recall", "f1"):
                assert 0 <= model[split][metric] <= 1
            assert np.array(model[split]["confusion_matrix"]).sum() == 400
    artifact = load_model(model_dir / "model.joblib")
    low = predict(artifact, {"attendance": 10, "internal_marks": 10, "assignment_score": 10})
    high = predict(artifact, {"attendance": 95, "internal_marks": 95, "assignment_score": 95})
    assert low["support_probability"] > high["support_probability"]
