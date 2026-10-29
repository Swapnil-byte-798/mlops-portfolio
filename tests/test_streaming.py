import json
from types import SimpleNamespace
from unittest.mock import Mock

import pytest
import requests


def record(value=None):
    return SimpleNamespace(topic="messages", partition=2, offset=17,
        value={"id": 4, "text": "free prize"} if value is None else value)


def test_commit_follows_broker_confirmation(stream, monkeypatch):
    events = []
    monkeypatch.setattr(stream, "predict", lambda text: {"label": "spam", "confidence": .7})
    consumer, producer = Mock(), Mock()
    producer.send.side_effect = lambda *a, **kw: SimpleNamespace(get=lambda **kw: events.append("ack"))
    consumer.commit.side_effect = lambda offsets: events.append(("commit", offsets))
    output = stream.process_record(record(), consumer, producer)
    assert events[0] == "ack" and events[1][0] == "commit"
    offsets = events[1][1]
    assert len(offsets) == 1
    partition, next_offset = next(iter(offsets.items()))
    assert (partition.topic, partition.partition, next_offset.offset) == ("messages", 2, 18)
    assert output["event_id"] == "messages:2:17"
    assert producer.send.call_args.kwargs["key"] == b"messages:2:17"


@pytest.mark.parametrize("stage", ["prediction", "send", "ack"])
def test_failure_never_commits_input(stream, monkeypatch, stage):
    consumer, producer = Mock(), Mock()
    prediction = Mock(return_value={"label": "spam", "confidence": .7})
    monkeypatch.setattr(stream, "predict", prediction)
    if stage == "prediction": prediction.side_effect = RuntimeError("API unavailable")
    elif stage == "send": producer.send.side_effect = RuntimeError("buffer unavailable")
    else: producer.send.return_value.get.side_effect = RuntimeError("broker rejected output")
    with pytest.raises(RuntimeError): stream.process_record(record(), consumer, producer)
    consumer.commit.assert_not_called()


@pytest.mark.parametrize("value", [[], "text", {}, {"text": None}, {"text": 8}])
def test_invalid_kafka_records_fail_before_ack(stream, monkeypatch, value):
    consumer, producer = Mock(), Mock()
    prediction = Mock()
    monkeypatch.setattr(stream, "predict", prediction)
    with pytest.raises(ValueError): stream.process_record(record(value), consumer, producer)
    consumer.commit.assert_not_called()
    prediction.assert_not_called()


def response(status, data=None):
    result = requests.Response()
    result.status_code = status
    result._content = json.dumps(data or {"label": "spam", "confidence": .7}).encode()
    return result


@pytest.mark.parametrize("status", [400, 401, 404, 422])
def test_permanent_http_error_is_not_retried(stream, monkeypatch, status):
    post = Mock(return_value=response(status))
    monkeypatch.setattr(stream.requests, "post", post)
    monkeypatch.setattr(stream.time, "sleep", lambda _: None)
    with pytest.raises(requests.HTTPError): stream.predict("message")
    assert post.call_count == 1


@pytest.mark.parametrize("first", [response(503), response(429), requests.ConnectionError("offline")])
def test_transient_http_error_is_retried(stream, monkeypatch, first):
    post = Mock(side_effect=[first, response(200)])
    monkeypatch.setattr(stream.requests, "post", post)
    monkeypatch.setattr(stream.time, "sleep", lambda _: None)
    assert stream.predict("message")["label"] == "spam"
    assert post.call_count == 2


def test_exhausted_api_failure_is_bounded(stream, monkeypatch):
    post = Mock(side_effect=requests.Timeout("timeout"))
    monkeypatch.setattr(stream.requests, "post", post)
    monkeypatch.setattr(stream.time, "sleep", lambda _: None)
    with pytest.raises(requests.Timeout): stream.predict("message")
    assert post.call_count == 3


@pytest.mark.parametrize("payload", [
    {"label": "other", "confidence": .5}, {"label": "spam", "confidence": float("nan")},
    {"label": "spam", "confidence": 2}, {"label": "spam", "confidence": True},
])
def test_invalid_api_response_is_not_published(stream, monkeypatch, payload):
    monkeypatch.setattr(stream.requests, "post", Mock(return_value=response(200, payload)))
    with pytest.raises(ValueError): stream.predict("message")


def test_automatic_offsets_are_disabled(stream, monkeypatch):
    constructor = Mock()
    monkeypatch.setattr(stream, "KafkaConsumer", constructor)
    stream.connect_consumer()
    assert constructor.call_args.kwargs["enable_auto_commit"] is False
