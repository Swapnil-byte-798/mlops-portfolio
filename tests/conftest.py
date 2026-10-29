import importlib.util
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


def load_module(relative, name):
    spec = importlib.util.spec_from_file_location(name, ROOT / relative)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="session")
def training():
    return load_module("serving/train.py", "training")


@pytest.fixture(scope="session")
def artifact(training, tmp_path_factory):
    directory = tmp_path_factory.mktemp("model")
    path = directory / "model.pkl"
    model, report = training.train(model_path=path, report_path=directory / "metadata.json")
    return path, model, report


@pytest.fixture
def stream():
    return load_module("kafka-streaming/consumer.py", "stream")
