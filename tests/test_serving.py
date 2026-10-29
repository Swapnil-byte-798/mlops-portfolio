import hashlib

import joblib
import pytest
from fastapi.testclient import TestClient

from conftest import load_module


@pytest.fixture
def client(artifact):
    module = load_module("serving/app.py", "serving")
    with TestClient(module.create_app(artifact[0])) as client:
        yield client


@pytest.mark.parametrize("text,label", [
    ("Congratulations you won a free prize claim now", "spam"),
    ("Hey are we still meeting for lunch tomorrow", "ham"),
])
def test_real_predictions(client, artifact, text, label):
    response = client.post("/predict", json={"text": text})
    assert response.status_code == 200
    result = response.json()
    model = artifact[1]
    assert result["label"] == label == model.predict([text])[0]
    assert result["confidence"] == round(float(model.predict_proba([text]).max()), 4)
    assert result["model_id"] == hashlib.sha256(artifact[0].read_bytes()).hexdigest()[:12]


@pytest.mark.parametrize("payload", [
    {}, {"text": None}, {"text": 123}, {"text": []}, {"text": ""},
    {"text": " \n\t"}, {"text": "a" * 10001}, {"text": "hi", "label": "spam"},
])
def test_invalid_requests_are_rejected(client, payload):
    assert client.post("/predict", json=payload).status_code == 422


def test_exact_text_limit_and_unknown_tokens(client):
    response = client.post("/predict", json={"text": "q" * 10000})
    assert response.status_code == 200
    assert response.json()["warning"] == "no_known_tokens"
    assert client.get("/health").status_code == 200
    assert client.get("/ready").status_code == 200


@pytest.mark.parametrize("corrupt", [False, True])
def test_missing_or_corrupt_model_does_not_look_ready(tmp_path, corrupt):
    path = tmp_path / "bad.pkl"
    if corrupt:
        path.write_bytes(b"not a model")
    module = load_module("serving/app.py", "bad_serving")
    with TestClient(module.create_app(path)) as client:
        assert client.get("/health").status_code == 200
        assert client.get("/ready").status_code == 503
        assert client.post("/predict", json={"text": "free prize"}).status_code == 503


def test_saved_pipeline_and_evaluation(artifact):
    path, model, report = artifact
    assert joblib.load(path).predict(["free prize"])[0] == model.predict(["free prize"])[0]
    assert report["rows"] == 40 and report["class_counts"] == {"ham": 20, "spam": 20}
    assert len(report["evaluation"]["accuracy"]["folds"]) == 5
    assert 0 <= report["evaluation"]["accuracy"]["mean"] <= 1
    assert report["model_sha256"] == hashlib.sha256(path.read_bytes()).hexdigest()


@pytest.mark.parametrize("content", [
    "text,label\nhello,ham\n", "label,text\nother,hello\n", "label,text\nham,   \n",
    "label,text\nham,hello\nspam,free prize\n",
])
def test_bad_training_data_is_rejected(training, tmp_path, content):
    path = tmp_path / "data.csv"
    path.write_text(content)
    with pytest.raises(ValueError):
        training.load_dataset(path)
