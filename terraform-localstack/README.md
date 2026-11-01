# Terraform and LocalStack

This independent exercise creates S3 bucket `mlops-model-artifacts` and DynamoDB table `predictions` (string key `id`, on-demand capacity) in a local AWS emulator. The serving and Kafka modules do not upload artifacts to this bucket or store predictions in this table.

## Run (from this directory)

Requirements: Docker Compose and Terraform >= 1.5. The CI check uses Terraform 1.9.8 and the locked AWS provider 5.100.0.

```bash
docker compose up -d
# Wait until http://localhost:4566/_localstack/health responds.
terraform init
terraform validate
terraform plan -out=plan.tfplan
terraform apply plan.tfplan
docker compose exec -T localstack awslocal s3api head-bucket --bucket mlops-model-artifacts
docker compose exec -T localstack awslocal dynamodb describe-table --table-name predictions
terraform plan -detailed-exitcode
```

A no-change plan exits 0; a proposed change exits 2. The provider has local endpoints and dummy test credentials, not a real AWS account. Keep state and real credentials out of Git.

For a deliberate provider-lock refresh across the supported desktop platforms, use `terraform providers lock -platform=linux_amd64 -platform=darwin_arm64 -platform=windows_amd64` and review the signed provider/checksum output. Do not disable checksum validation.

Destroy only this exercise's isolated resources when finished:

```bash
terraform destroy
docker compose down -v
```

Passing LocalStack checks demonstrates an emulated lifecycle, not an AWS deployment or a Terraform-managed Kubernetes cluster. See [verification](../docs/verification.md).
