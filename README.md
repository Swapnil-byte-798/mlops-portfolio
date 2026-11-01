# MLOps Portfolio

A Python operations demonstration around a TF-IDF + logistic-regression spam classifier. It includes an HTTP API, real Kafka inference, a Kubernetes deployment and a separate Terraform/LocalStack resource exercise.

**Scope:** 40 curated messages (20 ham, 20 spam), not a production spam benchmark. The five-fold fixture accuracy is 77.5%, with 12.25 percentage points of fold dispersion; mean spam recall is 65%. Training accuracy is 100% and is not a held-out result.

## Modules

| Module | What runs | Boundary |
|---|---|---|
| [Serving](serving/) | Model build, metadata and FastAPI inference | No production auth, monitoring or retraining |
| [Kafka](kafka-streaming/) | Messages -> HTTP model -> confirmed predictions | At least once; duplicate outputs remain possible |
| [Kubernetes](kubernetes/) | Two API replicas and model-aware probes | Tested on a local kind cluster |
| [Terraform](terraform-localstack/) | S3 bucket + DynamoDB table in LocalStack | Independent resources; application does not use them |
| [Bedrock](bedrock-explainer/) | Optional LLM interpretation of an API result | Mocked contract tests only; live AWS path unverified |

[Execution evidence and remaining limits](docs/verification.md). [Study material](docs/README.md) includes architecture, tools, analogies and interview Q&A. The refreshed [complete study guide](docs/MLOps_Portfolio_Study_Guide.pdf) replaces the earlier PDF.

## Run the Python path

Python 3.11 or 3.12:

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -r serving/requirements.txt
python serving/train.py
python -m uvicorn app:app --app-dir serving --host 127.0.0.1 --port 8767
```

In another terminal, use [http://localhost:8767/docs](http://localhost:8767/docs) or:

```bash
curl http://localhost:8767/ready
curl -X POST http://localhost:8767/predict \
  -H 'Content-Type: application/json' \
  -d '{"text":"Congratulations you won a free prize claim now"}'
```

On Windows activate with `.venv\Scripts\Activate.ps1`. Read each module README for Docker, Kafka, Terraform or Kubernetes instructions. They require Docker; Terraform and Kubernetes also need their respective CLIs. A real AWS account is needed only for the optional Bedrock call.

## Run the checks

```bash
python -m pip install -r kafka-streaming/requirements.txt -r bedrock-explainer/requirements.txt -r requirements-test.txt
python -m pytest tests -q
```

CI runs those tests on Python 3.11 and 3.12 and independently checks actual Kafka outputs/committed offsets, Terraform apply/verify/no-change-plan/destroy, and Kubernetes rollout/HTTP/pod replacement. Local regression mocks are fault-injection checks, not substitutes for these integration runs.

## API behavior

`/health` is process liveness. `/ready` requires the model; missing/corrupt artifacts return 503 from readiness and prediction. Train and restart to recover. Prediction requires a strict, nonblank string of at most 10,000 characters, with no extra fields; invalid requests return 422.

The response has `label`, `confidence`, `model_id` and `warning`. Confidence is an uncalibrated maximum class probability. Unknown-vocabulary text receives `no_known_tokens`; this does not establish an accurate prediction.

## Limits

The model uses a demonstration fixture with no real-world performance claim. There is no model registry, drift detector, automated retraining, dead-letter queue or downstream deduplicator. One broker with replication factor one is not a fault-tolerant Kafka cluster. Bedrock output would be an interpretation, not measured model feature attribution. LocalStack results are not a real AWS deployment.
