from __future__ import annotations

import os

KAFKA_SCHEMA_REGISTRY_URL = os.environ.get(
    "KAFKA_SCHEMA_REGISTRY_URL",
    "http://localhost:8081",
)
KAFKA_BOOTSTRAP_SERVERS = os.environ.get(
    "KAFKA_BOOTSTRAP_SERVERS",
    "localhost:9092",
)
DEFAULT_KAFKA_TOPIC = "market"
