from __future__ import annotations

import os

DEFAULT_STREAMLIT_PORT = int(os.environ.get("STREAMLIT_PORT", 8501))

KAFKA_BOOTSTRAP_SERVERS = os.environ.get(
    "KAFKA_BOOTSTRAP_SERVERS",
    "localhost:9092",
)

KAFKA_TOPIC_OHLC_5M = os.environ.get("KAFKA_TOPIC_OHLC_5M", "OHLC_5M")
KAFKA_TOPIC_OHLC_15M = os.environ.get("KAFKA_TOPIC_OHLC_15M", "OHLC_15M")
KAFKA_TOPIC_EMA_9 = os.environ.get("KAFKA_TOPIC_EMA_9", "EMA_9")
KAFKA_TOPIC_EMA_12 = os.environ.get("KAFKA_TOPIC_EMA_12", "EMA_12")
