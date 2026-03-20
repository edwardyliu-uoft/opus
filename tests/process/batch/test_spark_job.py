from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from opus.process.batch import spark_job


class _DummyColumn:
    def cast(self, _dtype: str):
        return self

    def isin(self, _items):
        return object()


class _DummyExpr:
    def alias(self, _name: str):
        return self


def _make_spark_session_mocks(
    parsed_df: MagicMock,
) -> tuple[MagicMock, SimpleNamespace]:
    spark = MagicMock()

    dataframe_kafka = MagicMock()
    dataframe_mid = MagicMock()
    dataframe_kafka.select.return_value = dataframe_mid
    dataframe_mid.select.return_value = parsed_df

    reader = MagicMock()
    reader.format.return_value = reader
    reader.option.return_value = reader
    reader.load.return_value = dataframe_kafka
    spark.read = reader

    builder = MagicMock()
    builder.appName.return_value = builder
    builder.master.return_value = builder
    builder.config.return_value = builder
    builder.getOrCreate.return_value = spark

    spark_session = SimpleNamespace(builder=builder)
    return spark, spark_session


def _write_schema(tmp_path: Path, topic: str = "OHLC_5M") -> None:
    (tmp_path / f"{topic}.json").write_text(
        json.dumps(
            {
                "ticker": "string",
                "window_start": "string",
                "window_end": "string",
                "open_price": "double",
                "high_price": "double",
                "low_price": "double",
                "close_price": "double",
                "volume": "long",
            }
        ),
        encoding="utf-8",
    )


def test_clear_local_spark_env_removes_known_vars(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("SPARK_HOME", "x")
    monkeypatch.setenv("SPARK_MASTER", "x")
    monkeypatch.setenv("PYSPARK_HOME", "x")
    monkeypatch.setenv("UNRELATED", "y")

    spark_job._clear_local_spark_env()

    assert "SPARK_HOME" not in spark_job.os.environ
    assert "SPARK_MASTER" not in spark_job.os.environ
    assert "PYSPARK_HOME" not in spark_job.os.environ
    assert spark_job.os.environ.get("UNRELATED") == "y"


def test_process_batch_returns_when_topics_filter_leaves_no_models(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    model = SimpleNamespace(topic="OHLC_5M")
    spark_session = SimpleNamespace(builder=MagicMock())

    monkeypatch.setattr(spark_job, "SimpleLinearRegression", lambda: model)
    monkeypatch.setattr(spark_job, "SparkSession", spark_session)

    spark_job.process_batch(topics=["SOME_OTHER_TOPIC"])

    spark_session.builder.appName.assert_not_called()


def test_process_batch_trains_and_predicts_happy_path(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    _write_schema(tmp_path)
    monkeypatch.setattr(spark_job, "DEFAULT_SCHEMAS_DIR", tmp_path)

    parsed_df = MagicMock()
    parsed_df.count.side_effect = [1, 1]
    predictions = MagicMock()

    model = MagicMock()
    model.name = "SimpleLinearRegression"
    model.topic = "OHLC_5M"
    model.tickers = []
    model.predict.return_value = predictions

    spark, spark_session = _make_spark_session_mocks(parsed_df)

    monkeypatch.setattr(spark_job, "SimpleLinearRegression", lambda: model)
    monkeypatch.setattr(spark_job, "SparkSession", spark_session)
    monkeypatch.setattr(spark_job, "col", lambda _name: _DummyColumn())
    monkeypatch.setattr(spark_job, "from_json", lambda *_args, **_kwargs: _DummyExpr())

    spark_job.process_batch()

    model.fit.assert_called_once_with(parsed_df)
    model.predict.assert_called_once_with(parsed_df)
    predictions.show.assert_called_once_with(10)
    spark.stop.assert_called_once()


def test_process_batch_skips_models_when_topic_has_no_data(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    _write_schema(tmp_path)
    monkeypatch.setattr(spark_job, "DEFAULT_SCHEMAS_DIR", tmp_path)

    parsed_df = MagicMock()
    parsed_df.count.return_value = 0

    model = MagicMock()
    model.name = "SimpleLinearRegression"
    model.topic = "OHLC_5M"
    model.tickers = []

    spark, spark_session = _make_spark_session_mocks(parsed_df)

    monkeypatch.setattr(spark_job, "SimpleLinearRegression", lambda: model)
    monkeypatch.setattr(spark_job, "SparkSession", spark_session)
    monkeypatch.setattr(spark_job, "col", lambda _name: _DummyColumn())
    monkeypatch.setattr(spark_job, "from_json", lambda *_args, **_kwargs: _DummyExpr())

    spark_job.process_batch()

    model.fit.assert_not_called()
    model.predict.assert_not_called()
    spark.stop.assert_called_once()


def test_process_batch_handles_kafka_read_failure_and_continues(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    _write_schema(tmp_path)
    monkeypatch.setattr(spark_job, "DEFAULT_SCHEMAS_DIR", tmp_path)

    model = MagicMock()
    model.name = "SimpleLinearRegression"
    model.topic = "OHLC_5M"
    model.tickers = []

    spark = MagicMock()
    reader = MagicMock()
    reader.format.return_value = reader
    reader.option.return_value = reader
    reader.load.side_effect = RuntimeError("kafka unavailable")
    spark.read = reader

    builder = MagicMock()
    builder.appName.return_value = builder
    builder.master.return_value = builder
    builder.config.return_value = builder
    builder.getOrCreate.return_value = spark
    spark_session = SimpleNamespace(builder=builder)

    monkeypatch.setattr(spark_job, "SimpleLinearRegression", lambda: model)
    monkeypatch.setattr(spark_job, "SparkSession", spark_session)

    spark_job.process_batch()

    model.fit.assert_not_called()
    model.predict.assert_not_called()
    spark.stop.assert_called_once()
