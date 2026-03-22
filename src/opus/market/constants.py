from __future__ import annotations

import os
from pathlib import Path

DEFAULT_DATA_DIR = Path(__file__).parents[3] / "data"

DEFAULT_SCHEMAS_DIR = Path(__file__).parent / "schemas"
DEFAULT_SCHEMA_PATH_MARKET_EVENT = DEFAULT_SCHEMAS_DIR / "market_event.avsc"

KAFKA_SCHEMA_REGISTRY_URL = os.environ.get(
    "KAFKA_SCHEMA_REGISTRY_URL",
    "http://localhost:8081",
)
KAFKA_BOOTSTRAP_SERVERS = os.environ.get(
    "KAFKA_BOOTSTRAP_SERVERS",
    "localhost:9092",
)
DEFAULT_KAFKA_TOPIC = "market"
