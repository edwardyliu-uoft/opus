import json
import logging
import signal
import sys
import time
from typing import Any, Dict

from confluent_kafka import Consumer, KafkaException, Message

# Try importing constants from package
try:
    from opus.ui.constants import (
        KAFKA_BOOTSTRAP_SERVERS,
        KAFKA_TOPIC_OHLC_5M,
        KAFKA_TOPIC_EMA_9,
        KAFKA_TOPIC_EMA_12,
    )
    from opus.ui.storage import RedisStorage
except ImportError:
    # Fallback for running as script
    sys.path.append("src")
    from opus.ui.constants import (
        KAFKA_BOOTSTRAP_SERVERS,
        KAFKA_TOPIC_OHLC_5M,
        KAFKA_TOPIC_EMA_9,
        KAFKA_TOPIC_EMA_12,
    )
    from opus.ui.storage import RedisStorage

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("opus-ingest")


class IngestWorker:
    def __init__(self, bootstrap_servers: str):
        self.running = True
        self.redis_client = RedisStorage(host="127.0.0.1", port=6379)
        self.topics = [KAFKA_TOPIC_OHLC_5M, KAFKA_TOPIC_EMA_9, KAFKA_TOPIC_EMA_12]

        conf = {
            "bootstrap.servers": bootstrap_servers,
            "group.id": "opus-redis-ingester",
            "auto.offset.reset": "earliest",
            "enable.auto.commit": False, 
        }
        self.consumer = Consumer(conf)
        self.consumer.subscribe(self.topics)

    def process_message(self, topic: str, msg_val: bytes):
        try:
            data = json.loads(msg_val.decode("utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError):
            logger.error(f"Failed to decode message from {topic}")
            return

        # Determine key prefix and score field based on topic
        if topic == KAFKA_TOPIC_OHLC_5M:
            prefix = "ohlc"
            score_key = "window_end"
        elif topic == KAFKA_TOPIC_EMA_9:
            prefix = "ema9"
            score_key = "snapshot_time"
        elif topic == KAFKA_TOPIC_EMA_12:
            prefix = "ema12"
            score_key = "snapshot_time"
        else:
            return

        ticker = data.get("ticker")
        if not ticker:
            return
            
        # Push to Redis Sorted Set
        # Score = timestamp
        # Member = entire json
        try:
            timestamp_str = data.get(score_key)
            if not timestamp_str:
                return
            
            # Simple ISO parsing for sorting score
            # ideally use numeric timestamp.
            # We use the helper in storage.py
            
            # Use RedisStorage helper
            if topic == KAFKA_TOPIC_OHLC_5M:
                self.redis_client.push_records("ohlc", [data], score_key="window_end")
                self.redis_client.register_ticker(ticker)
            elif topic == KAFKA_TOPIC_EMA_9:
                self.redis_client.push_records("ema9", [data], score_key="snapshot_time")
            elif topic == KAFKA_TOPIC_EMA_12:
                self.redis_client.push_records("ema12", [data], score_key="snapshot_time")

        except Exception as e:
            logger.error(f"Error processing message: {e}")

    def run(self):
        logger.info(f"Starting ingestion for topics: {self.topics}")
        try:
            while self.running:
                msg = self.consumer.poll(1.0)
                if msg is None:
                    continue

                if msg.error():
                    if msg.error().code() == -191: # _PARTITION_EOF
                        continue
                    else:
                        logger.error(msg.error())
                        continue

                self.process_message(msg.topic(), msg.value())
                # Commit offset after processing
                self.consumer.commit(message=msg, asynchronous=True)

        except KeyboardInterrupt:
            pass
        finally:
            logger.info("Closing consumer...")
            self.consumer.close()

def main():
    worker = IngestWorker(bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS)
    worker.run()

if __name__ == "__main__":
    main()