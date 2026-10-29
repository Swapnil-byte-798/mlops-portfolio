import io
import json
from unittest.mock import Mock

import pytest

from conftest import load_module


def test_bedrock_request_shape_without_live_aws(monkeypatch):
    module = load_module("bedrock-explainer/explain.py", "bedrock")
    client = Mock()
    client.invoke_model.return_value = {"body": io.BytesIO(json.dumps({
        "content": [{"type": "text", "text": "Possible interpretation."}]}).encode())}
    monkeypatch.setattr(module.boto3, "client", Mock(return_value=client))
    assert module.explain('free "prize"', "spam", .7) == "Possible interpretation."
    body = json.loads(client.invoke_model.call_args.kwargs["body"])
    assert body["anthropic_version"] == "bedrock-2023-05-31"
    assert "not measured feature attribution" in body["messages"][0]["content"]


@pytest.mark.parametrize("label,score", [("other", .7), ("spam", float("inf")), ("spam", -1)])
def test_invalid_prediction_never_calls_aws(monkeypatch, label, score):
    module = load_module("bedrock-explainer/explain.py", "invalid_bedrock")
    client = Mock()
    monkeypatch.setattr(module.boto3, "client", client)
    with pytest.raises(ValueError): module.explain("text", label, score)
    client.assert_not_called()
