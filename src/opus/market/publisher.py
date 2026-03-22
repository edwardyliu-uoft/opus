from __future__ import annotations

import csv
import gzip
import heapq
import logging
import time
from pathlib import Path

from confluent_kafka import Producer
from confluent_kafka.schema_registry import SchemaRegistryClient
from confluent_kafka.schema_registry.avro import AvroSerializer
from confluent_kafka.serialization import MessageField, SerializationContext

from .constants import (
    DEFAULT_DATA_DIR,
    DEFAULT_KAFKA_TOPIC,
    DEFAULT_SCHEMA_PATH_MARKET_EVENT,
    KAFKA_BOOTSTRAP_SERVERS,
    KAFKA_SCHEMA_REGISTRY_URL,
)
from .util import parse_timestamp

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MarketStream:
    def __init__(
        self,
        tickers: str | list[str],
        start_date: str,
        end_date: str,
        *,
        data_dir: str | Path | None = None,
        schema_path: str | Path | None = None,
    ):
        """Class that merges multiple CSV.gz streams for given tickers and date range, yielding rows in chronological order."""

        self.tickers: list[str] = (
            [ticker.strip() for ticker in tickers.split(",")]
            if isinstance(tickers, str)
            else tickers
        )
        self.start_date: str = start_date
        self.end_date: str = end_date

        self.data_dir: Path = (
            Path(data_dir) if data_dir is not None else DEFAULT_DATA_DIR
        )
        self.schema_path: Path = (
            Path(schema_path)
            if schema_path is not None
            else DEFAULT_SCHEMA_PATH_MARKET_EVENT
        )
        self.heap: list[tuple] = []
        self._initialize_streams()

    def _initialize_streams(self):
        """Extremely simplified representation of loading multiple ticker/date CSV.gz files

        Initializes the heap with the first row of each relevant CSV.gz file.
        Expecting `data_dir` to be present in the directory structure:
            data/year/yyyyMMdd/<ticker>.csv.gz

        The prompt implies a robust implementation, so we yield rows and heapify on Timestamp
        """

        # Discover files matching the date range and tickers, and push their first rows into the heap
        for year_dir in self.data_dir.glob("*"):
            # Only consider directories that match the year format expected in the path
            if not year_dir.is_dir():
                continue

            for date_dir in year_dir.glob("*"):
                # Only consider directories that match the date format expected in the path
                if not date_dir.is_dir():
                    continue

                # Check if date is within range
                if self.start_date <= date_dir.name <= self.end_date:
                    for ticker in self.tickers:
                        csv_gz_path = date_dir / f"{ticker}.csv.gz"
                        if csv_gz_path.exists():
                            # Open a stream and read the first row to heapify
                            self._heapify(csv_gz_path, ticker)

    def _heapify(self, csv_gz_path, ticker):
        csv_gz = gzip.open(csv_gz_path, "rt")
        csv_reader = csv.DictReader(csv_gz)
        try:
            row = next(csv_reader)
            ts_ns = parse_timestamp(row["Date"], row["Timestamp"])
            # Tuple: (Timestamp, Ticker, Row, Reader-Context)
            heapq.heappush(self.heap, (ts_ns, ticker, row, csv_reader, csv_gz))
        except StopIteration:
            csv_gz.close()

    def __iter__(self):
        return self

    def __next__(self):
        if not self.heap:
            raise StopIteration

        _, ticker, row, csv_reader, csv_gz = heapq.heappop(self.heap)

        # Advance the stream we just popped from
        try:
            next_row = next(csv_reader)
            ts_ns = parse_timestamp(next_row["Date"], next_row["Timestamp"])
            heapq.heappush(
                self.heap,
                (ts_ns, ticker, next_row, csv_reader, csv_gz),
            )
        except StopIteration:
            csv_gz.close()

        return row


def publish_market_events(
    tickers: str | list[str],
    start_date: str,
    end_date: str,
    speed: float,
    *,
    topic: str = DEFAULT_KAFKA_TOPIC,
    schema_path: str | Path | None = None,
):
    """Asynchronous playback loop that reads from MarketStream and produces to Kafka with Avro serialization."""

    # Setup Kafka Registry Client
    schema_registry_client = SchemaRegistryClient({"url": KAFKA_SCHEMA_REGISTRY_URL})
    schema_path = (
        Path(schema_path)
        if schema_path is not None
        else DEFAULT_SCHEMA_PATH_MARKET_EVENT
    )
    with open(schema_path) as avsc:
        schema = avsc.read()

    # Setup Avro Serializer
    avro_serializer = AvroSerializer(
        schema_registry_client,
        schema,
        lambda obj, ctx: obj,  # Pass direct dict
    )

    # Setup Kafka Producer
    producer = Producer({"bootstrap.servers": KAFKA_BOOTSTRAP_SERVERS})

    # Initialize MarketStream
    tickers = (
        [ticker.strip() for ticker in tickers.split(",")]
        if isinstance(tickers, str)
        else tickers
    )
    market_stream = MarketStream(tickers, start_date, end_date)

    # Log the start of playback with details
    logger.info(
        f"Starting playback for {tickers} from {start_date} to {end_date} at {speed}x speed."
    )

    # Playback loop with timing control based on event timestamps and speed multiplier
    event_ns = None
    real_ns = None
    for row in market_stream:
        event_time_ns = parse_timestamp(row["Date"], row["Timestamp"])
        row["Timestamp"] = event_time_ns
        row["Price"] = float(row["Price"])
        row["Quantity"] = int(row["Quantity"])

        if event_ns is None:
            event_ns = event_time_ns
            real_ns = time.time_ns()

        # Calculate the expected real execution time based on scaled event time
        simulated_elapsed_ns = (event_time_ns - event_ns) / float(speed)
        target_real_ns = real_ns + simulated_elapsed_ns

        current_real_ns = time.time_ns()
        drift_ns = target_real_ns - current_real_ns

        if drift_ns > 0:
            time.sleep(drift_ns / 1_000_000_000.0)

        # Serialize & Produce
        try:
            producer.produce(
                topic=topic,
                value=avro_serializer(
                    row,
                    SerializationContext(topic, MessageField.VALUE),
                ),
                on_delivery=lambda err, msg: (
                    logger.error(f"Failed: {err}")
                    if err
                    else logger.debug(f"Delivered: {msg.value()}")
                ),
            )
            # Poll asynchronously frequently to handle callbacks
            producer.poll(0)
        except BufferError:
            logger.error("Buffer full, waiting...")
            producer.poll(0.1)
            producer.produce(
                topic=topic,
                value=avro_serializer(
                    row,
                    SerializationContext(topic, MessageField.VALUE),
                ),
            )

    producer.flush()
    logger.info("Publishing complete.")
