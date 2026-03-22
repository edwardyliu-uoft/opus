from __future__ import annotations

import json
from unittest.mock import MagicMock, patch

from opus.ingest.redis_worker import RedisWorker


@patch("opus.ingest.redis_worker.redis.Redis")
def test_redis_worker_initialization(mock_redis):
    worker = RedisWorker(kafka_topics=["EMA", "OHLC"])
    assert worker.running is True
    assert worker.kafka_topic_map["EMA"] == "EMA"
    assert worker.kafka_topic_map["OHLC"] == "OHLC"


@patch("opus.ingest.redis_worker.redis.Redis")
def test_redis_worker_signal(mock_redis):
    worker = RedisWorker()
    worker._handle_signal(None, None)
    assert worker.running is False


@patch("opus.ingest.redis_worker.redis.Redis")
def test_redis_worker_process_message_ohlc(mock_redis):
    worker = RedisWorker()
    worker.kafka_topic_map["OHLC"] = "OHLC"

    mock_msg = MagicMock()
    mock_msg.error.return_value = None
    mock_msg.topic.return_value = "OHLC"
    mock_msg.value.return_value = json.dumps(
        {
            "ticker": "AAPL",
            "window_start": 100,
            "window_end": 200,
            "open_price": 1.0,
            "high_price": 2.0,
            "low_price": 0.5,
            "close_price": 1.5,
            "volume": 1000,
        }
    ).encode("utf-8")

    worker._process_message(mock_msg)

    worker.client.xadd.assert_called_once()
    args, _ = worker.client.xadd.call_args
    assert args[0] == "OHLC:AAPL"
    assert args[1]["open"] == 1.0


@patch("opus.ingest.redis_worker.redis.Redis")
def test_redis_worker_process_message_missing_ticker(mock_redis):
    worker = RedisWorker()
    mock_msg = MagicMock()
    mock_msg.error.return_value = None
    mock_msg.topic.return_value = "OHLC"
    mock_msg.value.return_value = json.dumps(
        {
            "open_price": 1.0,
        }
    ).encode("utf-8")

    worker._process_message(mock_msg)
    worker.client.xadd.assert_not_called()
