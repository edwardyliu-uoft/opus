from opus.process.stream.metrics.ema import ExponentialMovingAverage
from opus.process.stream.metrics.tumbling_ohlc import TumblingOHLC


def test_tumbling_ohlc_sql_generation():
    metric = TumblingOHLC(window=5, source_table="market_events")

    assert metric.name == "OHLC_5M"
    assert metric.target_table == "OHLC_5M"

    ddl = metric.flink_ddl()
    assert "CREATE TABLE OHLC_5M" in ddl
    assert "'topic' = 'OHLC_5M'" in ddl

    dml = metric.flink_dml()
    assert "INSERT INTO OHLC_5M" in dml
    assert "TUMBLE(event_time, INTERVAL '5' MINUTE)" in dml
    assert "FROM market_events" in dml


def test_exponential_moving_average_sql_generation():
    metric = ExponentialMovingAverage(periods=9, source_table="market_events")

    assert metric.name == "EMA_9"
    assert metric.target_table == "EMA_9"

    ddl = metric.flink_ddl()
    assert "CREATE TABLE EMA_9" in ddl
    assert "snapshot_time TIMESTAMP(3)" in ddl
    assert "'topic' = 'EMA_9'" in ddl

    dml = metric.flink_dml()
    assert "INSERT INTO EMA_9" in dml
    assert "AVG(Price) OVER" in dml
    assert "ROWS BETWEEN 8 PRECEDING AND CURRENT ROW" in dml
    assert "FROM market_events" in dml
