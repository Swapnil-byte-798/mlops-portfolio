# Kubernetes deployment

Deploy the serving image with two replicas. The startup and readiness probes use `/ready`, while liveness uses `/health`. A missing model cannot make the pod ready just because the HTTP process is alive.

## Run (from this directory)

Start a local Kubernetes cluster (kind, minikube or Docker Desktop), then:

```bash
docker build -t mlops-serving:latest ../serving
# For kind, use your cluster's actual name:
kind load docker-image mlops-serving:latest --name kind
kubectl apply -f deployment.yaml -f service.yaml
kubectl rollout status deployment/spam-api --timeout=180s
kubectl get pods -l app=spam-api
kubectl port-forward service/spam-api 8767:8000
```

In another terminal, request `http://localhost:8767/ready` or open `http://localhost:8767/docs`. The Service also declares NodePort 30080; local-cluster node networking varies, so the documented access path is port-forwarding.

CI uses a separate kind cluster named `mlops-test`, verifies two ready replicas and HTTP predictions, deletes one pod and checks replacement. This is a functional local-cluster check, not a multi-node availability or production scaling benchmark.

Clean up the resources you created:

```bash
kubectl delete -f service.yaml -f deployment.yaml
```

[Study notes](../docs/README.md) explain Deployments, Services, resource requests/limits and the three probe types.
