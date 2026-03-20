from __future__ import annotations

from unittest.mock import MagicMock

from opus.process.batch.models.simple_lr import SimpleLinearRegression


def test_simple_lr_metadata_properties() -> None:
    model = SimpleLinearRegression()

    assert model.name == "SimpleLinearRegression"
    assert model.topic == "OHLC_5M"
    assert model.tickers == ["AAPL"]


def test_fit_sets_model_and_fitted_flag(monkeypatch) -> None:
    model = SimpleLinearRegression()

    dataframe = MagicMock()
    dataframe_dropna = MagicMock()
    dataframe.dropna.return_value = dataframe_dropna

    assembler = MagicMock()
    lr = MagicMock()
    pipeline = MagicMock()
    pipeline_model = MagicMock()
    pipeline.fit.return_value = pipeline_model

    monkeypatch.setattr(
        "opus.process.batch.models.simple_lr.VectorAssembler",
        lambda **_kwargs: assembler,
    )
    monkeypatch.setattr(
        "opus.process.batch.models.simple_lr.LinearRegression", lambda **_kwargs: lr
    )
    monkeypatch.setattr(
        "opus.process.batch.models.simple_lr.Pipeline", lambda stages: pipeline
    )

    fitted = model.fit(dataframe)

    dataframe.dropna.assert_called_once()
    pipeline.fit.assert_called_once_with(dataframe_dropna)
    assert fitted is pipeline_model
    assert model.model is pipeline_model
    assert model.fitted is True


def test_predict_uses_trained_model_transform() -> None:
    model = SimpleLinearRegression()
    dataframe = MagicMock()
    predictions = MagicMock()

    trained_model = MagicMock()
    trained_model.transform.return_value = predictions
    model.model = trained_model
    model.fitted = True

    result = model.predict(dataframe)

    trained_model.transform.assert_called_once_with(dataframe)
    assert result is predictions
