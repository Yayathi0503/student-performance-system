"""Reproducible synthetic-data demonstration, with independent validation and test sets."""

import argparse
import json
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, confusion_matrix, f1_score, precision_score, recall_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

from app.services.prediction import FEATURES


def synthetic_data(rows=2000, seed=42):
    rng = np.random.default_rng(seed)
    frame = pd.DataFrame(rng.uniform(0, 100, (rows, 3)), columns=FEATURES)
    # Outcome is a noisy simulated support need, not an observed real-world outcome.
    latent = 0.35 * frame.attendance + 0.45 * frame.internal_marks + 0.20 * frame.assignment_score
    frame["needs_support"] = ((latent + rng.normal(0, 10, rows)) < 50).astype(int)
    return frame


def metrics(y, predicted):
    return {"accuracy": accuracy_score(y, predicted), "precision": precision_score(y, predicted, zero_division=0),
            "recall": recall_score(y, predicted, zero_division=0), "f1": f1_score(y, predicted, zero_division=0),
            "confusion_matrix": confusion_matrix(y, predicted, labels=[0, 1]).tolist()}


def train(output: Path, seed=42):
    output.mkdir(parents=True, exist_ok=True)
    frame = synthetic_data(seed=seed)
    x, y = frame[FEATURES], frame.needs_support
    x_train, x_holdout, y_train, y_holdout = train_test_split(x, y, test_size=0.4, stratify=y, random_state=seed)
    x_val, x_test, y_val, y_test = train_test_split(x_holdout, y_holdout, test_size=0.5, stratify=y_holdout, random_state=seed)
    models = {"logistic_regression": make_pipeline(StandardScaler(), LogisticRegression(solver="liblinear", random_state=seed)),
              "random_forest": RandomForestClassifier(n_estimators=150, max_depth=8, random_state=seed, n_jobs=1)}
    scores = {}
    for name, model in models.items():
        model.fit(x_train, y_train)
        scores[name] = {"validation": metrics(y_val, model.predict(x_val))}
    selected = max(scores, key=lambda name: scores[name]["validation"]["f1"])
    # Selection is finished before evaluating the held-out test set.
    for name, model in models.items():
        scores[name]["test"] = metrics(y_test, model.predict(x_test))
    artifact = {"schema_version": 1, "features": FEATURES, "name": selected, "model": models[selected], "seed": seed}
    joblib.dump(artifact, output / "model.joblib")
    report = {"data_source": "synthetic", "seed": seed, "rows": len(frame), "split": "60% train / 20% validation / 20% test",
              "selection": "Highest validation F1", "selected_model": selected, "models": scores,
              "confusion_matrix_order": "rows=true, columns=predicted; labels=[0,1]",
              "limitations": "Synthetic outcomes reflect a simulated rule, not clinical or educational validation."}
    (output / "metrics.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    pd.concat([x_test, y_test], axis=1).to_csv(output / "test_data.csv", index=False)
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=Path("artifacts"))
    args = parser.parse_args()
    print(json.dumps(train(args.output), indent=2))
