"""
Kafka Producer for Campus Cafe Customer Events
Generates random customer interaction events and sends them to Kafka using Schema Registry.
"""

import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from random import choice, randint, uniform

from confluent_kafka import SerializingProducer
from confluent_kafka.schema_registry import SchemaRegistryClient
from confluent_kafka.schema_registry.json_schema import JSONSerializer
from confluent_kafka.serialization import StringSerializer

# Mock data for generating random events
CUSTOMER_NAMES = [
    "Alice Johnson",
    "Bob Smith",
    "Charlie Davis",
    "Diana Martinez",
    "Ethan Brown",
]
DRINK_NAMES = [
    "Espresso",
    "Latte",
    "Cappuccino",
    "Americano",
    "Mocha",
    "Cold Brew",
    "Matcha Latte",
]


def generate_random_event():
    """Generate a random customer event conforming to the schema."""
    event = {
        "event_id": str(uuid.uuid4()),
        "customer_name": choice(CUSTOMER_NAMES),
        "drink_name": choice(DRINK_NAMES),
        "quantity": randint(1, 3),
        "amount": round(uniform(3.50, 8.99), 2),
        "is_member": choice([True, False]),
        "ts_utc": datetime.now(timezone.utc).isoformat(),
    }
    return event


def on_delivery(err, msg):
    """Callback function for message delivery reporting."""
    if err is not None:
        print(f"Delivery failed: {err}")
    else:
        print(f"Delivered: {msg.topic()} [{msg.partition()}] offset={msg.offset()}")


def main(bootstrap_servers: str, schema_registry_url: str, topic: str):
    """Main producer function."""

    # Schema Registry configuration
    schema_registry_conf = {"url": schema_registry_url}
    schema_registry_client = SchemaRegistryClient(schema_registry_conf)

    # Load schema from file
    schema_str = Path("customer_event.schema.json").read_text()

    # Serializer configuration
    def to_dict(obj, ctx):
        return obj

    # JSON Serializer configuration
    json_serializer = JSONSerializer(
        schema_str=schema_str,
        schema_registry_client=schema_registry_client,
        to_dict=to_dict,
    )

    # Producer configuration
    producer_conf = {
        "bootstrap.servers": bootstrap_servers,
        "client.id": "cafe-event-producer",
        "acks": 1,  # Wait for leader acknowledgment (balance between performance and durability)
        "key.serializer": StringSerializer("utf_8"),
        "value.serializer": json_serializer,
    }

    producer = SerializingProducer(producer_conf)

    print("Starting Cafe Event Producer with Schema Registry...")
    print(f"Generating and sending 5 random customer events to topic '{topic}'...\n")

    # Generate and send 5 random events
    for i in range(1, 6, 1):
        event = generate_random_event()

        # Send to Kafka (serialization is handled automatically by SerializingProducer)
        producer.produce(
            topic=topic,
            key=event["event_id"],
            value=event,
            on_delivery=on_delivery,
        )

        print(
            f"Event {i}: {event['customer_name']} ordered {event['quantity']}x {event['drink_name']} (${event['amount']} CAD) - Member: {event['is_member']}"
        )

        # Trigger on delivery callback
        producer.poll(0)
        time.sleep(0.2)

    # Wait for all messages to be delivered
    print("\nFlushing remaining messages...")
    producer.flush()

    print("All messages sent successfully!")


if __name__ == "__main__":
    main("localhost:9092", "http://localhost:8081", "demo")
