"""
Kafka Consumer for Campus Cafe Customer Events
Consumes and displays customer interaction events from Kafka using Schema Registry.
"""

import signal
from datetime import datetime
from pathlib import Path

from confluent_kafka import DeserializingConsumer, KafkaException
from confluent_kafka.schema_registry import SchemaRegistryClient
from confluent_kafka.schema_registry.json_schema import JSONDeserializer
from confluent_kafka.serialization import StringDeserializer

# Global flag for graceful shutdown
running = True


def signal_handler(sig, frame):
    """Handle Ctrl+C gracefully."""
    global running
    print("Shutting down consumer...")
    running = False


def main(bootstrap_servers: str, schema_registry_url: str, topic: str):
    """Main consumer function."""

    # Schema Registry configuration
    schema_registry_conf = {"url": schema_registry_url}
    schema_registry_client = SchemaRegistryClient(schema_registry_conf)

    # Load schema from file
    schema_str = Path("customer_event.schema.json").read_text()

    # Deserializer configuration
    def from_dict(obj, ctx):
        return obj

    # JSON Deserializer configuration
    json_deserializer = JSONDeserializer(
        schema_str=schema_str,
        schema_registry_client=schema_registry_client,
        from_dict=from_dict,
    )

    # Consumer configuration
    group_id = "cafe-event-consumer-group"
    consumer = DeserializingConsumer(
        {
            "bootstrap.servers": bootstrap_servers,
            "group.id": group_id,
            "auto.offset.reset": "earliest",
            "enable.auto.commit": False,
            "key.deserializer": StringDeserializer("utf_8"),
            "value.deserializer": json_deserializer,
        }
    )

    # Subscribe to topic
    consumer.subscribe([topic])
    print("Starting Cafe Event Consumer with Schema Registry...")
    print(f"Listening to topic '{topic}' (group: {group_id})...")
    print("Press Ctrl+C to stop\n")
    print("=" * 80)

    # Set up graceful shutdown
    signal.signal(signal.SIGINT, signal_handler)

    message_counter = 0
    try:
        while running:
            # Poll for messages (timeout in seconds)
            msg = consumer.poll(timeout=1.0)

            if msg is None:
                continue

            if msg.error():
                raise KafkaException(msg.error())

            # Deserialization is handled automatically by DeserializingConsumer
            event = msg.value()
            if event is None:
                continue

            # Extract metadata
            partition = msg.partition()
            offset = msg.offset()
            _, timestamp_ms = msg.timestamp()
            timestamp = datetime.fromtimestamp(timestamp_ms / 1000.0)

            # Display event with formatting
            print(f"Message #{message_counter + 1}")
            print(f"\t├─ Partition: {partition} | Offset: {offset}")
            print(f"\t├─ Kafka Timestamp: {timestamp.strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"\t├─ Event ID: {event['event_id']}")
            print(
                f"\t├─ Customer: {event['customer_name']} {'(Member)' if event['is_member'] else '(Non-Member)'}"
            )
            print(f"\t├─ Order: {event['quantity']}x {event['drink_name']}")
            print(f"\t├─ Amount: ${event['amount']:.2f}")
            print(f"\t└─ Event Time (UTC): {event['ts_utc']}")
            print("-" * 80)

            # Commit offsets after processing
            consumer.commit(asynchronous=False)

            # Counter increment
            message_counter += 1

    except Exception as e:
        print(f"Error: {e}")
    finally:
        # Clean shutdown
        print("Closing consumer...")
        consumer.close()
        print(f"Consumer closed. Total messages consumed: {message_counter}")


if __name__ == "__main__":
    main("localhost:9092", "http://localhost:8081", "demo")
