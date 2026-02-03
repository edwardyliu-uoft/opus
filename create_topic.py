"""
Python script to create the Kafka topic for the campus cafe event pipeline.
"""

from confluent_kafka.admin import AdminClient, NewTopic


def create_topic(topic: str, num_partitions: int, replication_factor: int):
    """Create a topic with the specified topic name, number of partitions, and replication factor."""
    admin_client = AdminClient({"bootstrap.servers": "localhost:9092"})

    topic = NewTopic(
        topic=topic,
        num_partitions=num_partitions,
        replication_factor=replication_factor,
    )
    # Create topic
    futures = admin_client.create_topics([topic])

    # Wait for operation to complete
    for topic_name, future in futures.items():
        try:
            future.result()
            print(
                f"Topic '{topic_name}' created successfully with {num_partitions} partitions and a replication factor of {replication_factor}."
            )
        except Exception as e:
            if "already exists" in str(e):
                print(f"Topic '{topic_name}' already exists!")
            else:
                print(f"Failed to create topic '{topic_name}': {e}")


if __name__ == "__main__":
    create_topic("demo", 3, 1)
