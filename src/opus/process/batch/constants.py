from __future__ import annotations

import os
from pathlib import Path

DEFAULT_SCHEMAS_DIR = Path(__file__).parent / "schemas"

KAFKA_BOOTSTRAP_SERVERS = os.environ.get(
    "KAFKA_BOOTSTRAP_SERVERS",
    "localhost:9092,kafka:29092",
)

SPARK_MASTER_URL = os.environ.get(
    "SPARK_MASTER_URL",
    "spark://localhost:7077",
)
