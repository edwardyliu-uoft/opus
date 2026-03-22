from __future__ import annotations

from unittest.mock import MagicMock

import pandas as pd

from opus.ui.services.redis_connector import RedisConnector


def test_redis_connector_init():
    conn = RedisConnector("localhost", 6379)
    assert conn.host == "localhost"
    assert conn.port == 6379
    assert conn.client is None


def test_as_dataframe_ohlc():
    conn = RedisConnector("localhost", 6379)
    df = pd.DataFrame(
        [
            {
                "open": "1.0",
                "high": "2.0",
                "low": "0.5",
                "close": "1.5",
                "volume": "1000",
                "end": "2023-01-01T00:00:00",
            }
        ]
    )
    result = conn._as_dataframe_ohlc(df)
    assert not result.empty
    assert result["open"].iloc[0] == 1.0
    assert "timestamp" in result.columns


def test_as_dataframe_ema():
    conn = RedisConnector("localhost", 6379)
    df = pd.DataFrame([{"ema": "100.5", "time": "2023-01-01T00:00:00"}])
    result = conn._as_dataframe_ema(df)
    assert not result.empty
    assert result["ema"].iloc[0] == 100.5
    assert "timestamp" in result.columns


def test_get_dataframe_ohlc_empty():
    conn = RedisConnector("localhost", 6379)
    conn.client = MagicMock()
    conn.client.xrevrange.return_value = []

    df = conn.get_dataframe_ohlc("AAPL")
    assert df.empty
