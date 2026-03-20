import gzip
from unittest.mock import MagicMock, patch

import pytest

from opus.market.publisher import MarketStream, publish_market_events


@pytest.fixture
def dummy_data_dir(tmp_path):
    """Creates a temporary directory structure mimicking the real data setup."""
    data_dir = tmp_path / "data"
    year_dir = data_dir / "2024"
    date_dir = year_dir / "20240101"
    date_dir.mkdir(parents=True)

    # Create dummy AAPL data
    aapl_file = date_dir / "AAPL.csv.gz"
    aapl_content = (
        "Date,Timestamp,EventType,Ticker,Price,Quantity,Exchange,Conditions\n"
        "2024-01-01,1000000000,TRADE,AAPL,150.0,10,NYSE,\n"
        "2024-01-01,3000000000,TRADE,AAPL,151.0,20,NYSE,\n"
    )
    with gzip.open(aapl_file, "wt") as f:
        f.write(aapl_content)

    # Create dummy MSFT data
    msft_file = date_dir / "MSFT.csv.gz"
    msft_content = (
        "Date,Timestamp,EventType,Ticker,Price,Quantity,Exchange,Conditions\n"
        "2024-01-01,2000000000,TRADE,MSFT,300.0,15,NASDAQ,\n"
        "2024-01-01,4000000000,TRADE,MSFT,305.0,25,NASDAQ,\n"
    )
    with gzip.open(msft_file, "wt") as f:
        f.write(msft_content)

    return data_dir


def test_market_stream_ordering(dummy_data_dir):
    """Test that MarketStream successfully interweaves multiple CSV streams in precise chronological order."""
    tickers = ["AAPL", "MSFT"]
    stream = MarketStream(
        data_dir=dummy_data_dir,
        tickers=tickers,
        start_date="20240101",
        end_date="20240101",
    )
    results = list(stream)
    assert len(results) == 4

    # Check if they are perfectly sorted by Timestamp
    timestamps = [int(r["Timestamp"]) for r in results]
    assert timestamps == [1000000000, 2000000000, 3000000000, 4000000000]

    # Check if the tickers map correctly
    assert results[0]["Ticker"] == "AAPL"
    assert results[1]["Ticker"] == "MSFT"
    assert results[2]["Ticker"] == "AAPL"
    assert results[3]["Ticker"] == "MSFT"


@patch("opus.market.publisher.Producer")
@patch("opus.market.publisher.SchemaRegistryClient")
@patch("opus.market.publisher.AvroSerializer")
@patch("opus.market.publisher.MarketStream")
@patch("opus.market.publisher.time.sleep")  # Mock sleep so the test runs instantly
def test_publish_market_events(
    _mock_sleep,
    MockMarketStream,
    MockAvroSerializer,
    MockSchemaRegistryClient,
    MockProducer,
):
    """Test the asynchronous playback loop, asserting it pushes to Kafka correctly."""

    # Setup our mock stream merger to return 2 dummy rows
    mock_merger_instance = MagicMock()
    mock_merger_instance.__iter__.return_value = iter(
        [
            {
                "Date": "2024-01-01",
                "Timestamp": "1000000000",
                "Price": "150.0",
                "Quantity": "10",
                "Ticker": "AAPL",
                "EventType": "TRADE",
            },
            {
                "Date": "2024-01-01",
                "Timestamp": "2000000000",
                "Price": "150.5",
                "Quantity": "15",
                "Ticker": "AAPL",
                "EventType": "TRADE",
            },
        ]
    )
    MockMarketStream.return_value = mock_merger_instance

    # Setup the mock Kafka Producer
    mock_producer_instance = MagicMock()
    MockProducer.return_value = mock_producer_instance

    # Setup mock AvroSerializer
    mock_avro_instance = MagicMock()
    mock_avro_instance.return_value = b"mocked_avro_bytes"
    MockAvroSerializer.return_value = mock_avro_instance

    # Run the publisher
    publish_market_events(
        tickers="AAPL",
        start_date="20240101",
        end_date="20240101",
        speed=1.0,
    )

    # It should have produced exactly 2 messages
    assert mock_producer_instance.produce.call_count == 2

    # Check the arguments to the first produce call
    call_args = mock_producer_instance.produce.call_args_list[0]
    assert call_args.kwargs["topic"] == "market"
    assert call_args.kwargs["value"] == b"mocked_avro_bytes"

    # It should flush at the end
    mock_producer_instance.flush.assert_called_once()
