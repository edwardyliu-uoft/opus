from __future__ import annotations

from pyspark.ml import Pipeline, PipelineModel
from pyspark.ml.feature import VectorAssembler
from pyspark.ml.regression import LinearRegression
from pyspark.sql import DataFrame

from .base import BaseModel


class SimpleLinearRegression(BaseModel):
    """
    A simple linear regression model that predicts the close_price
    based on open_price, high_price, low_price, and volume.
    """

    def __init__(self):
        super().__init__()

    @property
    def name(self) -> str:
        return "SimpleLinearRegression"

    @property
    def topic(self) -> str:
        return "OHLC_5M"

    @property
    def tickers(self):
        return ["AAPL"]

    def fit(self, dataframe: DataFrame) -> PipelineModel:
        # Drop rows with null values to avoid training errors
        dataframe_dropna = dataframe.dropna()

        # Assemble features into a single vector column
        assembler = VectorAssembler(
            inputCols=["open_price", "high_price", "low_price", "volume"],
            outputCol="features",
            handleInvalid="skip",
        )

        # Initialize Linear Regression model
        lr = LinearRegression(featuresCol="features", labelCol="close_price")

        # Create a Pipeline
        pipeline = Pipeline(stages=[assembler, lr])

        # Train the model
        model = pipeline.fit(dataframe_dropna)

        # Store the trained model and mark as fitted
        self.model = model
        self.fitted = True

        return model

    def predict(self, dataframe: DataFrame) -> DataFrame:
        """Make predictions using the trained model pipeline."""
        return self.model.transform(dataframe)
