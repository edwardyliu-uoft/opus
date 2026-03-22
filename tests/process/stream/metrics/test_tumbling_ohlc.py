from opus.process.stream.metrics.tumbling_ohlc import TumblingOHLC


def test_tumbling_ohlc_sql_generation():
    metric = TumblingOHLC(window=5, source_table="market_events")

    assert metric.name == "OHLC_5M"
    assert metric.target_table == "OHLC_5M"

    ddl = metric.flink_ddl()
    assert "CREATE TABLE IF NOT EXISTS OHLC_5M" in ddl
    assert "'topic' = 'OHLC_5M'" in ddl

    dml = metric.flink_dml()
    assert "INSERT INTO OHLC_5M" in dml
    assert "TUMBLE(event_time, INTERVAL '5' MINUTE)" in dml
    assert "FROM market_events" in dml
