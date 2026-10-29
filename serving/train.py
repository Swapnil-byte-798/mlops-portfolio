"""Evaluate the 40-message demo fixture, then fit and save the full pipeline."""
import csv
import hashlib
import json
from pathlib import Path

import joblib
import numpy as np
import sklearn
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, make_scorer, precision_score, recall_score, f1_score
from sklearn.model_selection import StratifiedKFold, cross_validate
from sklearn.pipeline import Pipeline

HERE = Path(__file__).parent
DATA = HERE / "data" / "messages.csv"
OUT = HERE / "model.pkl"
REPORT = HERE / "model_metadata.json"


def load_dataset(path=DATA):
    with open(path, newline="", encoding="utf-8") as stream:
        reader = csv.DictReader(stream)
        if reader.fieldnames != ["label", "text"]:
            raise ValueError("Expected CSV columns: label,text")
        rows = list(reader)
    if not rows or any(row["label"] not in {"ham", "spam"} or not row["text"].strip() for row in rows):
        raise ValueError("Every row needs a ham/spam label and nonblank text")
    texts, labels = [row["text"] for row in rows], [row["label"] for row in rows]
    if min(labels.count("ham"), labels.count("spam")) < 5:
        raise ValueError("Five-fold evaluation requires at least five examples of each class")
    if len(set(texts)) != len(texts):
        raise ValueError("Duplicate messages would leak across evaluation folds")
    return texts, labels


def build_pipeline():
    return Pipeline([
        ("tfidf", TfidfVectorizer(lowercase=True, stop_words="english")),
        ("lr", LogisticRegression(max_iter=1000, random_state=42)),
    ])


def train(data_path=DATA, model_path=OUT, report_path=REPORT):
    texts, labels = load_dataset(data_path)
    model = build_pipeline()
    scores = cross_validate(model, texts, labels,
        cv=StratifiedKFold(5, shuffle=True, random_state=42),
        scoring={"accuracy": "accuracy", **{
            name: make_scorer(fn, pos_label="spam", zero_division=0)
            for name, fn in [("spam_precision", precision_score), ("spam_recall", recall_score), ("spam_f1", f1_score)]
        }})
    model.fit(texts, labels)
    joblib.dump(model, model_path)
    report = {
        "dataset_kind": "manually curated demonstration fixture; not a real-world benchmark",
        "rows": len(texts), "class_counts": {label: labels.count(label) for label in ["ham", "spam"]},
        "data_sha256": hashlib.sha256(Path(data_path).read_bytes()).hexdigest(),
        "model_sha256": hashlib.sha256(Path(model_path).read_bytes()).hexdigest(),
        "sklearn_version": sklearn.__version__, "seed": 42,
        "training_accuracy": float(accuracy_score(labels, model.predict(texts))),
        "evaluation": {name.removeprefix("test_"): {
            "folds": values.tolist(), "mean": float(np.mean(values)), "std": float(np.std(values))
        } for name, values in scores.items() if name.startswith("test_")},
    }
    Path(report_path).write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))
    return model, report


if __name__ == "__main__":
    train()
