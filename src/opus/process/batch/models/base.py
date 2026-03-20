from __future__ import annotations

from abc import ABC, abstractmethod

from pyspark.ml import PipelineModel
from pyspark.sql import DataFrame


class BaseModel(ABC):
    """Base class for all machine learning models in Opus."""

    def __init__(self):
        self.fitted: bool = False
        self.model: PipelineModel | None = None

    @property
    @abstractmethod
    def name(self) -> str:
        """The logical name of the model (e.g. 'SimpleLinearRegression')."""
        pass

    @property
    @abstractmethod
    def topic(self) -> str:
        """The Kafka topic that this model consumes for training and prediction."""
        pass

    @property
    @abstractmethod
    def tickers(self) -> list[str]:
        """The ticker symbols that this model is designed to predict for (e.g. ['AAPL'])."""
        pass

    @abstractmethod
    def fit(self, dataframe: DataFrame) -> PipelineModel:
        """Train the model on the provided DataFrame."""
        pass

    @abstractmethod
    def predict(self, dataframe: DataFrame) -> DataFrame:
        """Make predictions using the fitted model on the provided DataFrame."""
        pass
