from opus.process.stream.metrics.ema import ExponentialMovingAverage


def test_exponential_moving_average_sql_generation():
    metric = ExponentialMovingAverage(periods=9, source_table="market_events")

    assert metric.name == "EMA_9"
    assert metric.target_table == "EMA_9"

    ddl = metric.flink_ddl()
    assert "CREATE TABLE IF NOT EXISTS EMA_9" in ddl
    assert "snapshot_time TIMESTAMP(3)" in ddl
    assert "'topic' = 'EMA_9'" in ddl

    dml = metric.flink_dml()
    assert "INSERT INTO EMA_9" in dml
    assert "AVG(Price) OVER" in dml
    assert "ROWS BETWEEN 8 PRECEDING AND CURRENT ROW" in dml
    assert "FROM market_events" in dml
