# Optional Bedrock interpretation

**Live AWS execution remains unverified.** The tests use a mocked SDK response to check request shape, response parsing and invalid-input rejection. They do not prove live access, quality or cost.

The CLI first requests an actual classifier prediction from the running API, then passes that label and score to Bedrock. The earlier hard-coded label/68% example has been removed. Its prompt identifies the result as a possible LLM interpretation, not measured feature attribution from logistic regression.

## Run (from this directory)

First run the serving API on host port 8767. You need an AWS account, externally configured credentials with suitable permissions, and access to your chosen Bedrock model in your region. Check the current AWS model availability for your account.

```bash
python -m pip install -r requirements.txt
export AWS_REGION=us-east-1
export BEDROCK_MODEL_ID=anthropic.claude-3-haiku-20240307-v1:0
python explain.py --text 'Congratulations you won a free prize claim now'
```

Use `--api http://localhost:8767/predict` if changing the service endpoint. Real requests may incur AWS charges. Never commit credentials.

A live invocation is optional and is not part of the repository's verified all-green local/emulated checks. For faithful classifier attribution, inspect fitted text features and coefficients or evaluate an appropriate attribution method; an LLM guess is not that evidence.
