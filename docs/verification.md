# MLOps Portfolio - execution audit

Audit date: 29 October 2026. Repository: https://github.com/Swapnil-byte-798/mlops-portfolio

**Verdict: the repaired local/emulated engineering paths pass. Live AWS Bedrock remains unverified. The classifier is a 40-message learning fixture, not a production-quality spam benchmark.**

Original revision: `ef1a3cc38b5f7fcf85670731e6ccd2f3a9352c8b`.
Repaired runtime revision: `6beb8978a1aaa7dd0e1d24ef1e4097b31adcf104`.
The documentation refresh follows that runtime revision without changing model data or the five module boundaries.

## What was actually executed

| Execution | Result |
|---|---|
| Original model training on supplied CSV | Passed; 40 records, 20 ham / 20 spam; 100% training accuracy |
| Original API with actual fitted model | Valid predictions worked; blank/oversized/extra-field inputs accepted |
| Original API with missing artifact | Health 200 while inference failed with 500 |
| Original Kafka client on workspace Python 3.12 | Import failed: missing kafka.vendor.six.moves |
| Original streaming control-flow fault injection | Auto-commit enabled; failed publication future not inspected |
| Repaired local Python regression suite | 44 passed, no skipped tests |
| Repaired CI Python 3.11 and 3.12 | 44 tests passed in each; actual Uvicorn HTTP checks passed |
| Real Kafka 3.9.0 / Docker Compose | Eight inputs produced; eight outputs read and validated; input offsets confirmed committed |
| Terraform 1.9.8 / AWS provider 5.100.0 / LocalStack | Validate, apply two resources, inspect both, empty second plan, destroy passed |
| Kubernetes on kind | Serving image built/loaded; two ready replicas; HTTP predictions; deleted pod replaced |
| Bedrock request/response contract | Mocked SDK tests passed; no live invocation |

Passing final runtime workflow: https://github.com/Swapnil-byte-798/mlops-portfolio/actions/runs/40877473684

The workspace has no Docker engine, Terraform CLI or Kubernetes cluster. Actual container/infrastructure executions therefore ran in GitHub Actions. Local API regression checks used FastAPI TestClient with the real model. A separate cross-process localhost probe in this workspace could not reach the background server; it is not counted as a local HTTP pass. The actual Uvicorn and container HTTP results above come from CI.

## Defects repaired

1. Added strict nonblank text validation, a 10,000-character limit and rejection of extra fields. Unknown-vocabulary messages retain the classifier output but expose a warning.
2. Replaced first-request lazy loading with per-process startup loading. Added model-aware readiness; missing/corrupt artifacts produce 503 from readiness and prediction. Liveness remains a separate process check.
3. Changed Kubernetes startup/readiness probes and container health to check the actual model readiness path.
4. Updated the Kafka client for Python 3.12 compatibility. Disabled automatic input commits, waited for confirmed output publication, then committed the exact partition's next offset.
5. Bounded transient HTTP retries; permanent 4xx failures now fail immediately. Added a finite producer mode for reproducible integration checks.
6. Added fixture evaluation inside training, with the complete TF-IDF/classifier Pipeline fitted separately in each fold. Saved metrics, versions, class counts and data/model hashes.
7. Made the optional Bedrock CLI obtain an actual API prediction instead of passing a fabricated sample label/68% score. Labelled LLM output as interpretation, not model feature attribution.
8. Committed signed provider checksums for Linux amd64, macOS ARM and Windows amd64; verified a read-only Terraform init on a fresh CI checkout.
9. Replaced outdated README/study claims and added repeatable regression and real-infrastructure CI checks.

## Failures retained during diagnosis

The first new integration run, https://github.com/Swapnil-byte-798/mlops-portfolio/actions/runs/40875951930, was not an all-clear. Terraform installed the locked provider but validation rejected the cached package against the committed checksums. The platform hashes were refreshed through the signed provider registry and committed; checksum verification was not disabled.

That run's independent Kafka output observer timed out. The actual consumer logs showed all eight successful predictions. The observer had a new-topic discovery race; creating both topics before starting the observer and reducing its metadata-refresh interval fixed the acceptance path. The passing check reads the actual output topic and confirms committed offsets; it does not merely accept console logs.

A second run passed with signed checksum generation. The final run above passed with the updated lock already committed and read-only init, so the final result does not depend on silently repairing the checkout during CI.

## Model quality and data scope

The supplied CSV contains 40 unique, curated-looking examples; no external dataset provenance or representative production sample is supplied. Data SHA-256:
`42f9bd25c10daa46b082f9674654ffd009884482ecb46b7beefea7f36e1e69c4`.

| Repaired training evaluation | Value |
|---|---:|
| Stratified folds / seed | 5 / 42 |
| Training/test records per fold | 32 / 8 |
| Fold accuracies | 87.5%, 87.5%, 62.5%, 87.5%, 62.5% |
| Mean accuracy | 77.50% |
| Fold accuracy standard deviation | 12.25 percentage points |
| Mean spam precision | 86.67% |
| Mean spam recall | 65.00% |
| Mean spam F1 | 0.7429 |
| Full-fixture training accuracy | 100.00% |

Standard deviation across folds is not a confidence interval. A separate audit-only stratified 32/8 split at seed 42 scored 100%; it is retained as a small-sample sensitivity example, not chosen as the headline. The final serving artifact fits all 40 records after evaluation. No synthetic replacement training set, real-world benchmark claim or model-family substitution was introduced.

## What the tests mean

Regression checks cover real classifier predictions/persistence, malformed requests, missing/corrupt artifacts, unknown-token warnings, invalid training files, commit ordering, publication/API failure without input commit, permanent/transient HTTP failure behavior and invalid response values. Kafka/boto3 mocks are explicitly fault/contract tests.

The independent integration jobs use an actual Kafka broker, API containers, LocalStack APIs and a kind Kubernetes cluster. They verify functional paths. They do not measure throughput, latency SLOs, distributed failover, security hardening or model performance on real traffic.

## Remaining limitations

- One broker with replication factor one; no distributed durability demonstration.
- At-least-once processing can duplicate outputs after a crash between publication and input commit. Stable event IDs are provided; downstream deduplication is not implemented.
- Invalid or persistently failing records stop the consumer without acknowledging the record. No dead-letter queue, automatic poison-record policy or recovery supervisor.
- S3 and DynamoDB resources are independent exercises. The app loads its artifact from the container filesystem and does not persist predictions there.
- No model registry, drift detector, automatic retraining, production authentication, global request-body policy or rate limiter.
- Some transitive packages and image tags remain floating; no bit-for-bit rebuild guarantee.
- Bedrock requires real account/model access and may be billable. Only mocked contract checks were run. An LLM interpretation is not faithful feature attribution.
- Forty curated messages are too small and unrepresentative to support a production spam-quality claim.

**Resume decision:** suitable as a scoped, tested MLOps learning demonstration. Describe the real integration checks and repaired reliability behavior; do not call it a production-ready classifier, a complete integrated AWS platform or a verified live Bedrock application.

Testing stops after this project. The next project requires the user's approval.

