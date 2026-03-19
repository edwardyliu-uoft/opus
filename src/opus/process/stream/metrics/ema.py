from __future__ import annotations

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
    ):
        """
        Args:
            periods (int): The number of periods to use for the EMA calculation (default: 9).
        """
        self.periods = periods

        super().__init__(source_table=source_table, target_table=target_table)

    @property
    def name(self) -> str:
        return f"EMA_{self.periods}"

    def flink_ddl(self) -> str:
        return f"""
        CREATE TABLE IF NOT EXISTS {self.target_table} (
            Ticker STRING,
            snapshot_time TIMESTAMP(3),
            ema_value DOUBLE
        ) WITH (
            'connector' = 'kafka',
            'topic' = '{self.target_table}',
            'properties.bootstrap.servers' = '{KAFKA_BOOTSTRAP_SERVERS}',
            'format' = 'json'
        )
        """

    def flink_dml(self) -> str:
        return f"""
        INSERT INTO {self.target_table}
        SELECT
            Ticker,
            event_time AS snapshot_time,
            AVG(Price) OVER (
                PARTITION BY Ticker
                ORDER BY event_time
                ROWS BETWEEN {self.periods - 1} PRECEDING AND CURRENT ROW
            ) AS ema_value
        FROM {self.source_table}
        """
