from __future__ import annotations

import json
import logging
import signal

import redis
from confluent_kafka import Consumer, KafkaError, Message

from opus.ingest.constants import DEFAULT_KAFKA_TOPICS

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class RedisWorker:
    def __init__(
        self,
        *,
        host: str = "localhost",
        port: int = 6379,
        kafka_topics: list[str] = None,
        kafka_bootstrap_servers: str = "localhost:9092",
        kafka_group_id: str = "ingest-redis",
        kafka_auto_offset_reset: str = "latest",
    ):
        self.client = redis.Redis(
            host=host,
            port=port,
            decode_responses=True,
        )
        self.kafka_consumer_configs = {
            "bootstrap.servers": kafka_bootstrap_servers,
            "group.id": kafka_group_id,
            "auto.offset.reset": kafka_auto_offset_reset,
        }
        self.kafka_topics = kafka_topics or DEFAULT_KAFKA_TOPICS
        self.running = True

        # Determine topic map based on topic names or configuration
        # For simplicity, we'll try to detect the type based on the topic name suffix or prefix
        self.kafka_topic_map = {}
        for kafka_topic in self.kafka_topics:
            kafka_topic_upper = kafka_topic.upper()
            if "EMA" in kafka_topic_upper:
                self.kafka_topic_map[kafka_topic] = "EMA"
            elif "OHLC" in kafka_topic_upper:
                self.kafka_topic_map[kafka_topic] = "OHLC"
            else:
                logger.warning(f"Unknown topic type for {kafka_topic}, skipping.")

    def _handle_signal(self, signum, frame):
        logger.info("Signal received, shutting down...")
        self.running = False

    def _process_message(self, message: Message):
        if message.error():
            if message.error().code() == KafkaError._PARTITION_EOF:
                return
            else:
                logger.error(f"Kafka error: {message.error()}")
                return

        try:
            topic = message.topic()
            value = message.value()
            if not value:
                return

            data = json.loads(value.decode("utf-8"))

            ticker = data.get("ticker")
            if not ticker:
                logger.warning(
                    f"Message in topic `{topic}` missing `ticker` field: {data}"
                )
                return

            stream_key = f"{topic}:{ticker}"
            message_type = self.kafka_topic_map.get(topic)
            if message_type == "OHLC":
                entry = {
                    "start": data.get("window_start"),
                    "end": data.get("window_end"),
                    "open": data.get("open_price"),
                    "high": data.get("high_price"),
                    "low": data.get("low_price"),
                    "close": data.get("close_price"),
                    "volume": data.get("volume"),
                }

                # Filter for None values
                entry = {k: v for k, v in entry.items() if v is not None}

                # Add to Redis Stream
                self.client.xadd(stream_key, entry, maxlen=1000)
                logger.debug(f"Pushed OHLC to `{stream_key}`: {entry}")

            elif message_type == "EMA":
                entry = {
                    "ema": data.get("ema_value"),
                    "time": data.get("snapshot_time"),
                }

                # Filter for None values
                entry = {k: v for k, v in entry.items() if v is not None}

                # Add to Redis Stream
                self.client.xadd(stream_key, entry, maxlen=1000)
                logger.debug(f"Pushed EMA to `{stream_key}`: {entry}")

        except json.JSONDecodeError:
            logger.error(f"Failed to decode JSON from {message.topic()}")
        except Exception as err:
            logger.error(f"Error processing message: {err}")

    def run(self):
        consumer = Consumer(self.kafka_consumer_configs)
        consumer.subscribe(self.kafka_topics)

        # Register signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self._handle_signal)
        signal.signal(signal.SIGTERM, self._handle_signal)

        logger.info(
            f"Starting redis worker; consuming from topics: {self.kafka_topics}"
        )

        try:
            while self.running:
                message = consumer.poll(1.0)
                if message is None:
                    continue
                self._process_message(message)
        finally:
            logger.info("Closing consumer...")
            consumer.close()


def ingest_redis(
    host: str = "localhost",
    port: int = 6379,
    kafka_topics: list[str] = None,
    kafka_bootstrap_servers: str = "localhost:9092",
    kafka_group_id: str = "ingest-redis",
    kafka_auto_offset_reset: str = "latest",
):
    ingestor = RedisWorker(
        host=host,
        port=port,
        kafka_topics=kafka_topics,
        kafka_bootstrap_servers=kafka_bootstrap_servers,
        kafka_group_id=kafka_group_id,
        kafka_auto_offset_reset=kafka_auto_offset_reset,
    )
    ingestor.run()
