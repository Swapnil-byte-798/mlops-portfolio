"""CI acceptance: read eight outputs from real Kafka and verify committed inputs."""
import json
import time

from kafka import KafkaConsumer, TopicPartition

consumer = KafkaConsumer("predictions", bootstrap_servers="kafka:9092",
    auto_offset_reset="earliest", enable_auto_commit=False,
    group_id=None, consumer_timeout_ms=120_000,
    value_deserializer=lambda value: json.loads(value.decode()))
results = {}
try:
    for record in consumer:
        value = record.value
        results[value["id"]] = value
        if len(results) == 8:
            break
finally:
    consumer.close()
assert set(results) == set(range(8)), results
for number, result in results.items():
    assert result["label"] == ("spam" if number % 2 == 0 else "ham"), result
    assert 0 <= result["confidence"] <= 1
    assert result["event_id"].startswith("messages:")
    assert result["model_id"]
offsets = KafkaConsumer(bootstrap_servers="kafka:9092", group_id="spam-inference",
    enable_auto_commit=False)
try:
    expected = {}
    for result in results.values():
        topic, partition, offset = result["event_id"].rsplit(":", 2)
        key = TopicPartition(topic, int(partition))
        expected[key] = max(expected.get(key, 0), int(offset) + 1)
    deadline = time.monotonic() + 15
    while time.monotonic() < deadline:
        committed = {key: offsets.committed(key) for key in expected}
        if all(committed[key] is not None and committed[key] >= value for key, value in expected.items()):
            break
        time.sleep(.5)
    else:
        raise AssertionError({"expected": expected, "committed": committed})
finally:
    offsets.close()
print(json.dumps({"result": "PASS", "predictions": list(results.values()),
    "verified_count": len(results), "input_offsets_committed": True}, indent=2))
