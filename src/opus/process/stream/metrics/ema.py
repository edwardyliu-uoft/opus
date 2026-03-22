from __future__ import annotations

import os

from ..constants import DEFAULT_KAFKA_TOPIC, KAFKA_BOOTSTRAP_SERVERS
from .base import BaseMetric


class ExponentialMovingAverage(BaseMetric):
    """
    Approximates an EMA calculation using PyFlink SQL OVER windows.

    Note:
    Pure recursive EMA in stateless SQL is complex, so we typically approximate with a bounded PRECEDING window.
    For true EMA, a stateful UDF or external state management would be needed.
    """

    def __init__(
        self,
        periods: int = 9,
        *,
        source_table: str = DEFAULT_KAFKA_TOPIC,
        target_table: str | None = None,
        ticker_column: str = "ticker",
        timestamp_column: str = "window_end",
        value_column: str = "close_price",
    ):
        """
        Args:
            periods (int): The number of periods to use for the EMA calculation (default: 9).
        """
        self.periods = periods
        self.ticker_column = ticker_column
        self.timestamp_column = timestamp_column
        self.value_column = value_column

        super().__init__(source_table=source_table, target_table=target_table)

    @property
    def name(self) -> str:
        return f"{self.source_table}_EMA_{self.periods}"

    def flink_ddl(self) -> str:
        return f"""
        CREATE TABLE IF NOT EXISTS {self.target_table} (
            ticker STRING,
            snapshot_time TIMESTAMP(3),
            ema_value DOUBLE
        ) WITH (
            'connector' = 'kafka',
            'topic' = '{self.target_table}',
            'properties.bootstrap.servers' = '{KAFKA_BOOTSTRAP_SERVERS}',
            'properties.group.id' = '{self.source_table.lower()}-ema-{self.periods}-{os.urandom(4).hex()}',
            'scan.startup.mode' = 'earliest-offset',
            'format' = 'json'
        )
        """

    def flink_dml(self) -> str:
        return f"""
        INSERT INTO {self.target_table}
        SELECT
            {self.ticker_column} as ticker,
            {self.timestamp_column} AS snapshot_time,
            AVG({self.value_column}) OVER (
                PARTITION BY {self.ticker_column}
                ORDER BY {self.timestamp_column}
                ROWS BETWEEN {self.periods - 1} PRECEDING AND CURRENT ROW
            ) AS ema_value
        FROM {self.source_table}
        """
