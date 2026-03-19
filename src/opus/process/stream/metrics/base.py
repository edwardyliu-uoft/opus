from __future__ import annotations

from abc import ABC, abstractmethod

from ..constants import DEFAULT_KAFKA_TOPIC


class BaseMetric(ABC):
    """
    Abstract base class for metric calculators.
    Creates an extensible architecture where adding a new metric is simplified.
    """

    def __init__(
        self,
        source_table: str = DEFAULT_KAFKA_TOPIC,
        target_table: str | None = None,
    ):
        self.source_table = source_table
        self.target_table = target_table or self.name

    @property
    @abstractmethod
    def name(self) -> str:
        """The logical name of the metric (e.g. 'OHLC_5MIN', 'EMA_9')."""
        pass

    @abstractmethod
    def flink_ddl(self) -> str:
        """Generates the Flink SQL required to create the target table for this metric."""
        pass

    @abstractmethod
    def flink_dml(self) -> str:
        """Generates the Flink SQL required to compute this metric from the source table
        and insert it into the target table.
        """
        pass
