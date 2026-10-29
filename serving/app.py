"""Spam-demo API with distinct process liveness and model readiness."""
from contextlib import asynccontextmanager
import hashlib
import logging
from pathlib import Path

import joblib
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, ConfigDict, Field, field_validator

MODEL_PATH = Path(__file__).with_name("model.pkl")
log = logging.getLogger(__name__)


class Message(BaseModel):
    model_config = ConfigDict(extra="forbid")
    text: str = Field(strict=True, min_length=1, max_length=10_000)

    @field_validator("text")
    @classmethod
    def require_nonblank(cls, value):
        if not value.strip():
            raise ValueError("text must contain a non-whitespace character")
        return value


def create_app(model_path=MODEL_PATH):
    @asynccontextmanager
    async def lifespan(application):
        application.state.model = None
        application.state.model_id = None
        try:
            path = Path(model_path)
            model = joblib.load(path)  # Only load the trusted artifact we trained.
            model.predict(["startup verification"])
            application.state.model = model
            application.state.model_id = hashlib.sha256(path.read_bytes()).hexdigest()[:12]
        except Exception:
            log.exception("Model startup failed; readiness will return 503")
        yield
        application.state.model = None

    application = FastAPI(title="Spam Classifier Demo API", version="1.1.0", lifespan=lifespan)

    def require_model():
        model = getattr(application.state, "model", None)
        if model is None:
            raise HTTPException(503, "Model unavailable; train the artifact and restart the service")
        return model

    @application.get("/health")
    def health():
        return {"status": "ok"}

    @application.get("/ready")
    def ready():
        require_model()
        return {"status": "ready", "model_id": application.state.model_id}

    @application.post("/predict")
    def predict(msg: Message):
        model = require_model()
        features = model.named_steps["tfidf"].transform([msg.text])
        probabilities = model.named_steps["lr"].predict_proba(features)[0]
        index = int(probabilities.argmax())
        return {
            "text": msg.text,
            "label": str(model.classes_[index]),
            "confidence": round(float(probabilities[index]), 4),
            "model_id": application.state.model_id,
            "warning": "no_known_tokens" if features.nnz == 0 else None,
        }

    return application


app = create_app()
