from datetime import datetime
from unittest.mock import MagicMock

from opus.ui.app import build_single_ticker_series, poll_json


class _FakeMessage:
    def __init__(self, payload=None, error=None):
        self._payload = payload
        self._error = error

    def error(self):
        return self._error

    def value(self):
        return self._payload


def test_poll_json_collects_only_valid_json_rows():
    mock_consumer = MagicMock()
    mock_consumer.poll.side_effect = [
        _FakeMessage(
            b'{"ticker":"AAPL","snapshot_time":"2026-03-20T10:00:00","ema_value":181.2}'
        ),
        _FakeMessage(b"not-json"),
        _FakeMessage(error="boom"),
        None,
        None,
        None,
        None,
    ]

    consumer_factory = MagicMock(return_value=mock_consumer)
    diagnostics = {}

    rows = poll_json(
        "EMA_9",
        bootstrap_servers="localhost:9092",
        max_messages=10,
        timeout_seconds=0.01,
        max_idle_rounds=4,
        diagnostics=diagnostics,
        consumer_factory=consumer_factory,
    )

    assert rows == [
        {
            "ticker": "AAPL",
            "snapshot_time": "2026-03-20T10:00:00",
            "ema_value": 181.2,
        }
    ]
    mock_consumer.subscribe.assert_called_once_with(["EMA_9"])
    mock_consumer.close.assert_called_once()
    assert diagnostics["topic"] == "EMA_9"
    assert diagnostics["rows"] == 1
    assert diagnostics["message_errors"] == 1
    assert diagnostics["decode_failures"] == 1


def test_build_single_ticker_series_joins_candles_and_ema_snapshots():
    price_rows = [
        {
            "ticker": "AAPL",
            "window_end": "2026-03-20T10:05:00",
            "open_price": 180.2,
            "high_price": 181.4,
            "low_price": 179.9,
            "close_price": 181.0,
        }
    ]
    ema9_rows = [
        {
            "ticker": "AAPL",
            "snapshot_time": "2026-03-20T10:05:00",
            "ema_value": 180.7,
        }
    ]
    ema12_rows = [
        {
            "ticker": "AAPL",
            "snapshot_time": "2026-03-20T10:05:00",
            "ema_value": 180.3,
        }
    ]

    candles, ema9_points, ema12_points = build_single_ticker_series(
        price_rows,
        ema9_rows,
        ema12_rows,
        ticker="AAPL",
        max_points=10,
    )

    assert len(candles) == 1
    assert len(ema9_points) == 1
    assert len(ema12_points) == 1

    candle = candles[0]
    assert candle["timestamp"] == datetime.fromisoformat("2026-03-20T10:05:00")
    assert candle["open"] == 180.2
    assert candle["high"] == 181.4
    assert candle["low"] == 179.9
    assert candle["close"] == 181.0

    ema9 = ema9_points[0]
    assert ema9["timestamp"] == datetime.fromisoformat("2026-03-20T10:05:00")
    assert ema9["value"] == 180.7

    ema12 = ema12_points[0]
    assert ema12["timestamp"] == datetime.fromisoformat("2026-03-20T10:05:00")
    assert ema12["value"] == 180.3
