# Serving the spam demo

The image trains a TF-IDF/logistic-regression Pipeline on the committed 40-message fixture. It also writes fold metrics and artifact/data hashes to `model_metadata.json`. Five-fold evaluation fits preprocessing inside each training fold; the final serving model then fits all 40 records.

## Docker run (from repository root)

```bash
docker build -t mlops-serving:latest serving
docker run -d -p 8767:8000 --name spam-api mlops-serving:latest
curl http://localhost:8767/ready
curl -X POST http://localhost:8767/predict \
  -H 'Content-Type: application/json' \
  -d '{"text":"free prize claim now"}'
docker rm -f spam-api
```

For a Python-only run, use the [root README](../README.md). The model loads once in each process's startup lifespan. There is no promised 40-second first-request delay; measure your environment.

`/health` checks process liveness; `/ready` requires a loaded model. Docker health uses readiness. A failed load leaves readiness and prediction at 503 until the artifact is fixed and the process restarts. Only load trusted joblib artifacts.

Requests require one nonblank string, at most 10,000 characters; extra fields are rejected. Unknown tokens get a warning. The returned probability is uncalibrated. This is a demo API with no production authentication, rate limiting or model-quality guarantee.

See [verification](../docs/verification.md) and [study material](../docs/README.md).
