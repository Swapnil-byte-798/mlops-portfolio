# Kafka inference

A real single-node Apache Kafka broker runs in KRaft mode. The producer writes to `messages`; the consumer calls the model API and writes to `predictions`. Clients use container-network address `kafka:9092`; this is not a configured host-client listener.

## Run (from this directory)

```bash
docker compose up --build
```

Broker and API health checks gate dependent startup. The default producer streams eight demonstration texts repeatedly. To run the finite acceptance scenario:

```bash
docker compose up -d --build --wait kafka spam-api
docker compose exec -T kafka /opt/kafka/bin/kafka-topics.sh --bootstrap-server kafka:9092 --create --if-not-exists --topic messages --partitions 1 --replication-factor 1
docker compose exec -T kafka /opt/kafka/bin/kafka-topics.sh --bootstrap-server kafka:9092 --create --if-not-exists --topic predictions --partitions 1 --replication-factor 1
docker compose up -d --build consumer
docker compose run --rm -T producer python producer.py --count 8 --interval 0.05
docker compose run --rm --no-deps -T consumer python - < ../scripts/check_stream.py
docker compose logs consumer
docker compose down -v
```

Use a fresh isolated stack for this check; retained offsets/messages from an earlier infinite producer change the scenario. The acceptance script reads all eight real output records, checks their labels and verifies committed input offsets.

## Delivery and failures

Automatic input commits are disabled. The consumer waits for `send(...).get(...)` to confirm the output, then commits the exact input partition at offset + 1. This is **at least once**: a crash between output acknowledgement and input commit can duplicate the output. Stable `event_id` values support future deduplication; no deduplicating sink is implemented.

Temporary network/429/5xx failures are retried up to three times. Permanent 4xx errors propagate immediately. Invalid records or persistent failures stop the consumer without committing that record. There is no dead-letter queue or automatic poison-record recovery. A single broker and replication factor one do not demonstrate distributed durability.

The Python client now supports the checked Python 3.11/3.12 environments. See [study material](../docs/README.md) for offsets, groups and listener explanations.
