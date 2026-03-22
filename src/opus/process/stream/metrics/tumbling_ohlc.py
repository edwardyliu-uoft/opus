from __future__ import annotations

import os

from ..constants import DEFAULT_KAFKA_TOPIC, KAFKA_BOOTSTRAP_SERVERS
from .base import BaseMetric


class TumblingOHLC(BaseMetric):
    """Calculates OHLC (Open, High, Low, Close) and Volume for each ticker in tumbling windows."""

    def __init__(
        self,
        window: int = 5,
        *,
        source_table: str = DEFAULT_KAFKA_TOPIC,
        target_table: str | None = None,
    ):
        """
        Args:
            window (int): The size of the tumbling window in minutes (default: 5).
        """
        self.window = window

        super().__init__(source_table=source_table, target_table=target_table)

    @property
    def name(self) -> str:
        return f"OHLC_{self.window}M"

    def flink_ddl(self) -> str:
        return f"""
        CREATE TABLE IF NOT EXISTS {self.target_table} (
            ticker STRING,
            window_start TIMESTAMP(3),
            window_end TIMESTAMP(3),
            open_price DOUBLE,
            high_price DOUBLE,
            low_price DOUBLE,
            close_price DOUBLE,
            volume BIGINT,
            WATERMARK FOR window_end AS window_end - INTERVAL '5' SECOND
        ) WITH (
            'connector' = 'kafka',
            'topic' = '{self.target_table}',
            'properties.bootstrap.servers' = '{KAFKA_BOOTSTRAP_SERVERS}',
            'properties.group.id' = 'ohlc-{self.window}m-{os.urandom(4).hex()}',
            'scan.startup.mode' = 'earliest-offset',
            'format' = 'json'
        )
        """

    def flink_dml(self) -> str:
        return f"""
        INSERT INTO {self.target_table}
        SELECT
            Ticker as ticker,
            TUMBLE_START(event_time, INTERVAL '{self.window}' MINUTE) AS window_start,
            TUMBLE_END(event_time, INTERVAL '{self.window}' MINUTE) AS window_end,
            FIRST_VALUE(Price) AS open_price,
            MAX(Price) AS high_price,
            MIN(Price) AS low_price,
            LAST_VALUE(Price) AS close_price,
            SUM(Quantity) AS volume
        FROM {self.source_table}
        GROUP BY
            Ticker,
            TUMBLE(event_time, INTERVAL '{self.window}' MINUTE)
        """
