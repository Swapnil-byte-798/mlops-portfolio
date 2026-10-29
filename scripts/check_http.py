"""Smoke-test the actual HTTP service, including validation and model readiness."""
import argparse
import json
import time
import urllib.error
import urllib.request

parser = argparse.ArgumentParser()
parser.add_argument("--url", default="http://localhost:8767")
args = parser.parse_args()
deadline = time.monotonic() + 120
while True:
    try:
        with urllib.request.urlopen(args.url + "/ready", timeout=3) as response:
            ready = json.load(response)
        assert ready["status"] == "ready"
        break
    except (OSError, AssertionError):
        if time.monotonic() >= deadline:
            raise
        time.sleep(1)
results = []
for text, expected in [("free prize claim now", "spam"),
                       ("meeting for lunch tomorrow", "ham"), ("   ", 422)]:
    request = urllib.request.Request(args.url + "/predict",
        data=json.dumps({"text": text}).encode(), headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(request, timeout=10) as response:
            result = json.load(response)
        assert result["label"] == expected, result
        results.append(result)
    except urllib.error.HTTPError as error:
        assert error.code == expected
        results.append({"input": text, "status": error.code})
print(json.dumps({"ready": ready, "cases": results, "result": "PASS"}, indent=2))
