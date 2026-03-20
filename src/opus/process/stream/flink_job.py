from __future__ import annotations

import logging
import os

from confluent_kafka.admin import AdminClient, NewTopic
from pyflink.table import EnvironmentSettings, TableEnvironment

from opus.process.stream.metrics.base import BaseMetric

from .constants import KAFKA_BOOTSTRAP_SERVERS, KAFKA_SCHEMA_REGISTRY_URL
from .metrics import ExponentialMovingAverage, TumblingOHLC

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def _clear_local_flink_env() -> None:
    """Clear Flink-related environment variables that can override runtime behavior."""

    flink_envars = [
        "FLINK_MASTER",
        "FLINK_HOME",
        "PYFLINK_HOME",
        "FLINK_CONF_DIR",
        "FLINK_LOG_DIR",
        "FLINK_LOCAL_DIRS",
        "FLINK_WORKER_DIR",
    ]
    for envar in flink_envars:
        if os.environ.pop(envar, None) is not None:
            logger.info("Removed environment variable override: %s", envar)


def _create_kafka_topic_if_not_exists(
    topic_name: str,
    *,
    bootstrap_servers: str = KAFKA_BOOTSTRAP_SERVERS,
):
    """
    Verify if a Kafka topic exists, if not create it.
    """
    admin_client = AdminClient({"bootstrap.servers": bootstrap_servers})
    metadata = admin_client.list_topics(timeout=10)

    if topic_name not in metadata.topics:
        logger.info(f"Topic '{topic_name}' does not exist. Creating it...")
        new_topic = NewTopic(topic_name, num_partitions=1, replication_factor=1)
        futures = admin_client.create_topics([new_topic])

        for topic, future in futures.items():
            try:
                future.result()
                logger.info(f"Topic '{topic}' created successfully.")
            except Exception as err:
                logger.error(f"Failed to create topic '{topic}': {err}")
    else:
        logger.info(f"Topic '{topic_name}' already exists.")


def process_stream(create_topics: bool = False):
    """
    Initializes the PyFlink streaming environment;
    Sets up the source/sink Kafka tables;
    and Executes the SQL for all registered metrics continuously.
    """
    logger.info("Starting Flink Stream Processing...")

    # Ensure no local Flink environment variables interfere with the TableEnvironment configuration
    _clear_local_flink_env()

    # 1. Setup table environment; streaming mode
    env_settings = EnvironmentSettings.in_streaming_mode()
    table_env = TableEnvironment.create(env_settings)

    # Configure Idle Timeout:
    # This ensures that when the historical data finishes publishing (leaving the Kafka source idle),
    # Flink doesn't stall the watermarks. It will automatically advance and flush the final pending metrics.
    table_env.get_config().set("table.exec.source.idle-timeout", "5000 ms")

    # Add the required jars for Kafka and Avro to the Flink TableEnvironment
    jars_dir = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "../../../../lib")
    )
    table_env.get_config().set(
        "pipeline.jars",
        f"file:///{jars_dir}/flink-sql-connector-kafka-4.0.1-2.0.jar;"
        f"file:///{jars_dir}/flink-sql-avro-confluent-registry-2.2.0.jar;"
        f"file:///{jars_dir}/flink-avro-2.2.0.jar;"
        f"file:///{jars_dir}/flink-sql-avro-2.2.0.jar",
    )
    # Important Note: Flink requires the Kafka SQL Connector JAR and Avro Confluent Registry JAR to be present.
    # In a production setup, it is suggested to inject this via the `pipeline.jars` config or to place it in the Flink `/lib` folder.

    # 2. Define the unified `market_events` data source table; reading from Kafka Avro
    source_ddl = f"""
        CREATE TABLE IF NOT EXISTS market_events (
            `Date` STRING,
            `Timestamp` BIGINT,
            `EventType` STRING,
            `Ticker` STRING,
            `Price` DOUBLE,
            `Quantity` INT,
            `Exchange` STRING,
            `Conditions` STRING,
            -- Define event time and watermarks using the nanosecond timestamp
            event_time AS TO_TIMESTAMP(FROM_UNIXTIME(`Timestamp` / 1000000000)),
            WATERMARK FOR event_time AS event_time - INTERVAL '2' SECOND
        ) WITH (
            'connector' = 'kafka',
            'topic' = 'market',
            'properties.bootstrap.servers' = '{KAFKA_BOOTSTRAP_SERVERS}',
            'properties.group.id' = 'process-stream-{os.urandom(4).hex()}',
            'scan.startup.mode' = 'earliest-offset',
            'format' = 'avro-confluent',
            'avro-confluent.schema-registry.url' = '{KAFKA_SCHEMA_REGISTRY_URL}'
        )
    """
    table_env.execute_sql(source_ddl)

    # 3. Register and execute the extensible metrics list
    # Each metric defines its own target table DDL and DML.
    # By passing the source table name, they know what to select from.
    metrics: list[BaseMetric] = [
        TumblingOHLC(window=5, source_table="market_events"),
        TumblingOHLC(window=15, source_table="market_events"),
        ExponentialMovingAverage(periods=9, source_table="market_events"),
        ExponentialMovingAverage(periods=12, source_table="market_events"),
    ]

    statement_set = table_env.create_statement_set()

    logger.info("Registering metric pipelines...")
    for metric in metrics:
        # Pre-create the target Kafka topic
        if create_topics:
            _create_kafka_topic_if_not_exists(
                metric.target_table,
                bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
            )

        logger.info(f" -> Injecting target table DDL for {metric.name}")
        # Create the target sink table for this specific metric
        table_env.execute_sql(metric.flink_ddl())

        logger.info(f" -> Adding DML logic to statement set for {metric.name}")
        # Add the insert query to the statement set to run them simultaneously
        statement_set.add_insert_sql(metric.flink_dml())

    logger.info("Submitting Job to Flink Cluster...")
    # Executing the statement set submits the asynchronous Flink job
    res = statement_set.execute()
    logger.info("Job submitted successfully. Real-time stream processing is active.")

    # Wait for the streaming job to finish (which is never, unless cancelled or failed)
    res.wait()
