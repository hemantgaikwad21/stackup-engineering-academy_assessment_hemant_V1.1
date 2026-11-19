"""
=============================================================
StackUp Engineering Academy — Data Engineering Assessment
Starter File: kafka_starter.py
Pillar: Big Data Processing — Task 3.2
=============================================================

SCENARIO
--------
The project management platform emits real-time events whenever key actions
occur (escalations, status changes, budget updates). Instead of batch files,
these now arrive as a live Kafka stream.

You will build a producer that simulates the event stream and a consumer
that reads, processes, and writes events to a local sink.

ARCHITECTURE
------------
  Simulator → [Kafka Topic: presight.project.events] → Consumer → outputs/kafka/

TASKS
-----
  Task 3.2a → Configure Kafka producer and consumer (see config below)
  Task 3.2b → Implement the producer to stream events from the JSONL file
  Task 3.2c → Implement the consumer to read and process events
  Task 3.2d → Consumer must: filter high-severity escalations and write them
               to a separate topic: presight.escalations.critical
  Task 3.2e → Write a summary of consumed events to outputs/kafka/summary.json

HOW TO RUN
----------
  Ensure Kafka is running (docker-compose up -d)

  Terminal 1 — Producer:
    python starter_files/kafka_starter.py --mode producer

  Terminal 2 — Consumer:
    python starter_files/kafka_starter.py --mode consumer

  Or run both in the same process (for testing):
    python starter_files/kafka_starter.py --mode both
"""

import json
import os
import time
import argparse
import logging
from datetime import datetime
from kafka import KafkaProducer, KafkaConsumer, consumer, consumer, producer
from kafka.admin import KafkaAdminClient, NewTopic
from kafka.admin import NewTopic

# TODO: Install kafka-python → pip install kafka-python
# from kafka import KafkaProducer, KafkaConsumer, KafkaAdminClient
# from kafka.admin import NewTopic

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)
logger = logging.getLogger(__name__)

# ── Paths ──────────────────────────────────────────────────────────────────────
BASE_DIR = os.path.dirname(
    os.path.dirname(
        os.path.dirname(os.path.abspath(__file__))
    )
)
EVENTS_FILE     = os.path.join(BASE_DIR, "datasets", "events_stream", "events_2025_01.jsonl")
OUTPUT_DIR      = os.path.join(BASE_DIR, "outputs", "kafka")
os.makedirs(OUTPUT_DIR, exist_ok=True)

# ── Kafka config ───────────────────────────────────────────────────────────────
KAFKA_BOOTSTRAP  = "localhost:9092"
TOPIC_EVENTS     = "presight.project.events"
TOPIC_ESCALATIONS = "presight.escalations.critical"


# ==============================================================================
# SETUP — Create Kafka topics
# ==============================================================================

def create_topics():

    admin = KafkaAdminClient(
        bootstrap_servers=KAFKA_BOOTSTRAP,
        client_id="presight-admin"
    )

    topics = [
        NewTopic(
            name=TOPIC_EVENTS,
            num_partitions=3,
            replication_factor=1
        ),
        NewTopic(
            name=TOPIC_ESCALATIONS,
            num_partitions=1,
            replication_factor=1
        )
    ]

    try:
        admin.create_topics(
            new_topics=topics,
            validate_only=False
        )

        logger.info("Kafka topics created")

    except Exception as e:
        logger.info(f"Topics already exist or error: {e}")

    finally:
        admin.close()


# ==============================================================================
# PRODUCER
# ==============================================================================

def build_producer():
    """
    Build and return a KafkaProducer.

    TODO:
      - Bootstrap to KAFKA_BOOTSTRAP
      - Serialise message values as JSON (utf-8 encoded)
      - Set a sensible request_timeout_ms
    """
    # YOUR CODE HERE
    producer = KafkaProducer(
    bootstrap_servers=KAFKA_BOOTSTRAP,
    value_serializer=lambda v:
        json.dumps(v).encode("utf-8"),
    key_serializer=lambda k:
        k.encode("utf-8"),
    request_timeout_ms=30000
)

    return producer


def run_producer(producer, events_file: str, delay_seconds: float = 0.00005):
    """
    Read events from the JSONL file and produce them to Kafka one by one,
    simulating a real-time stream.

    TODO:
      - Read each line from events_file
      - Parse it as JSON
      - Add a 'produced_at' timestamp to the message
      - Send to TOPIC_EVENTS using event_type as the message key
      - Log each message sent (event_id and event_type)
      - Sleep delay_seconds between messages to simulate stream rate
      - Flush and close the producer when done
    """
    logger.info("Starting producer — streaming events from: %s", events_file)
    sent_count = 0 
    with open(events_file, "r", encoding="utf-8") as f:
          for line in f:

            event = json.loads(line)

            event["produced_at"] = (
            datetime.utcnow().isoformat()
        )

            producer.send(
            TOPIC_EVENTS,
            key=event["event_type"],
            value=event
        )
            sent_count += 1
            if sent_count % 100 == 0:
              logger.info(
                "Sent %s messages. Latest event_id=%s",
                sent_count,
                event.get("event_id")
            )

            time.sleep(delay_seconds)

    logger.info("Total messages sent: %s", sent_count)


    producer.flush()
    producer.close()

logger.info("Producer completed successfully")


# ==============================================================================
# CONSUMER
# ==============================================================================

def build_consumer(topic: str):
    """
    Build and return a KafkaConsumer subscribed to a given topic.

    TODO:
      - Bootstrap to KAFKA_BOOTSTRAP
      - Set group_id to 'presight-assessment-consumer'
      - Deserialise message values from JSON
      - Set auto_offset_reset to 'earliest' (so we read from the beginning)
      - Set consumer_timeout_ms to 10000 (stop after 10s of no messages)
    """
    # YOUR CODE HERE
    consumer = KafkaConsumer(
    topic,
    bootstrap_servers=KAFKA_BOOTSTRAP,
    group_id="presight-assessment-consumer",
    value_deserializer=lambda m: json.loads(m.decode("utf-8")),
    auto_offset_reset="earliest",
    consumer_timeout_ms=10000
)

    return consumer


def run_consumer(consumer):
    """
    Consume events from TOPIC_EVENTS and process them.

    TODO:
      - Consume all messages from the topic
      - For each message:
          a) Log the event_id, event_type, and project_id
          b) If event_type == 'escalation_raised' AND severity == 'Critical':
               → Forward to TOPIC_ESCALATIONS (produce a new message)
          c) Accumulate a summary dict:
               { event_type: count } for all consumed messages
      - After consuming, write the summary to outputs/kafka/summary.json
      - Return the summary dict
    """
    logger.info("Starting consumer — listening on: %s", TOPIC_EVENTS)

    summary = {}
    start_time = time.time()

    # YOUR CODE HERE
    producer = build_producer()
    message_count = 0
    forwarded_count = 0 
    for message in consumer:

      event = message.value
      message_count += 1

      if message_count % 100 == 0:
        logger.info(
        "Consumed %s messages. Latest event_id=%s",
        message_count,
        event.get("event_id")
    )

      event_type = event.get("event_type")

      summary[event_type] = summary.get(event_type, 0) + 1

      if (
        event.get("event_type") == "escalation_raised"
        and event.get("payload", {}).get("severity") == "Critical"
    ):
        forwarded_count += 1

        producer.send(
            TOPIC_ESCALATIONS,
            key="critical",
            value=event
        )

        logger.info(
            "Forwarded critical escalation: %s",
            event.get("event_id")
        )

    producer.flush()
    producer.close()
    consumer.close()
    logger.info( "Total messages consumed: %s",    message_count)

    elapsed_time = time.time() - start_time

    throughput = (
    message_count / elapsed_time
    if elapsed_time > 0
    else 0)

    logger.info(
    "Throughput: %.2f messages/sec",
    throughput
      )


    # Write summary
    summary_path = os.path.join(OUTPUT_DIR, "summary.json")
    with open(summary_path, "w") as f:
        json.dump({
    "run_at": datetime.utcnow().isoformat(),
    "topic": TOPIC_EVENTS,
    "total_messages_consumed": message_count,
    "critical_escalations_forwarded": forwarded_count,
    "throughput_messages_per_second": round(throughput, 2),
    "event_counts": summary}, f, indent=2)
    logger.info("Summary written to: %s", summary_path)

    return summary


# ==============================================================================
# ENTRY POINT
# ==============================================================================

def main():
    parser = argparse.ArgumentParser(description="Kafka assessment — producer/consumer")
    parser.add_argument(
        "--mode",
        choices=["producer", "consumer", "both"],
        default="both",
        help="Run as producer, consumer, or both"
    )
    args = parser.parse_args()

    create_topics()

    if args.mode == "producer":
        producer = build_producer()
        run_producer(producer, EVENTS_FILE)

    elif args.mode == "consumer":
        consumer = build_consumer(TOPIC_EVENTS)
        run_consumer(consumer)

    elif args.mode == "both":
        # For testing: produce first, then consume
        producer = build_producer()
        run_producer(producer, EVENTS_FILE)

        consumer = build_consumer(TOPIC_EVENTS)
        summary  = run_consumer(consumer)
        print("\nEvent summary:", json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
