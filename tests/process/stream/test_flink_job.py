from unittest.mock import MagicMock, call, patch

from pyflink.table import TableEnvironment

from opus.process.stream.constants import KAFKA_BOOTSTRAP_SERVERS
from opus.process.stream.flink_job import process_stream


@patch("opus.process.stream.flink_job._create_kafka_topic_if_not_exists")
@patch("opus.process.stream.flink_job.TableEnvironment")
@patch("opus.process.stream.flink_job.EnvironmentSettings")
def test_process_stream_initialization_and_submission(
    mock_env_settings,
    mock_table_env_class,
    mock_create_topic,
):
    """
    Test that the process_stream function correctly initializes the Flink environment,
    creates the necessary source and sink tables, prepares the statement set, and submits it.
    """
    # Mocking Flink components
    mock_settings_instance = MagicMock()
    mock_env_settings.in_streaming_mode.return_value = mock_settings_instance

    mock_table_env_instance = MagicMock(spec=TableEnvironment)
    mock_table_env_class.create.return_value = mock_table_env_instance

    mock_statement_set = MagicMock()
    mock_table_env_instance.create_statement_set.return_value = mock_statement_set

    # Execute the streaming processor
    process_stream(create_topics=True)

    # Assert TableEnvironment was created correctly
    mock_env_settings.in_streaming_mode.assert_called_once()
    mock_table_env_class.create.assert_called_once_with(mock_settings_instance)

    # Assert execute_sql was called for the source table + 3 metrics sinks = 4 times
    assert mock_table_env_instance.execute_sql.call_count == 4

    # Check some of the execute_sql calls
    execute_args = [
        args[0][0] for args in mock_table_env_instance.execute_sql.call_args_list
    ]

    # 1. First call should be the source table DDL
    assert "CREATE TABLE IF NOT EXISTS market_events" in execute_args[0]

    # 2. Next calls should be DDLs for the metrics sinks
    assert "CREATE TABLE IF NOT EXISTS OHLC_5M" in execute_args[1]
    assert "CREATE TABLE IF NOT EXISTS OHLC_5M_EMA_9" in execute_args[2]
    assert "CREATE TABLE IF NOT EXISTS OHLC_5M_EMA_12" in execute_args[3]

    # Assert statements were added to the statement set
    assert mock_statement_set.add_insert_sql.call_count == 3

    insert_args = [
        args[0][0] for args in mock_statement_set.add_insert_sql.call_args_list
    ]
    assert "INSERT INTO OHLC_5M" in insert_args[0]
    assert "INSERT INTO OHLC_5M_EMA_9" in insert_args[1]
    assert "INSERT INTO OHLC_5M_EMA_12" in insert_args[2]

    # Assert Flink Job execution was submitted via statement_set.execute()
    mock_statement_set.execute.assert_called_once()

    # Verify that the topics are being pre-created using AdminClient
    assert mock_create_topic.call_count == 3
    mock_create_topic.assert_has_calls(
        [
            call("OHLC_5M", bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS),
            call("OHLC_5M_EMA_9", bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS),
            call("OHLC_5M_EMA_12", bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS),
        ],
        any_order=True,
    )
