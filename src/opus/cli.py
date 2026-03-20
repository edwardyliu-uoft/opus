import argparse

from opus.market.publisher import publish_market_events
from opus.process.batch.spark_job import process_batch
from opus.process.stream.flink_job import process_stream
from opus.ui import ui_ingest, ui_app


def main():
    # CLI Argument Parsing
    parser = argparse.ArgumentParser(description="Opus CLI")
    subparsers = parser.add_subparsers(dest="command")

    # > Market Parser
    market_parser = subparsers.add_parser("market")
    market_subparsers = market_parser.add_subparsers(dest="market_command")
    # > Market Publish Command
    market_publish_parser = market_subparsers.add_parser("publish")
    market_publish_parser.add_argument(
        "tickers",
        help="Ticker or comma-separated list of tickers",
    )
    market_publish_parser.add_argument(
        "--start",
        dest="start_date",
        required=True,
        help="Start date (yyyyMMdd)",
    )
    market_publish_parser.add_argument(
        "--end",
        dest="end_date",
        required=True,
        help="End date (yyyyMMdd)",
    )
    market_publish_parser.add_argument(
        "--speed",
        type=float,
        default=1.0,
        help="Playback speed multiplier",
    )

    # > Process Parser
    process_parser = subparsers.add_parser("process")
    process_subparsers = process_parser.add_subparsers(dest="process_command")

    # > Process Stream Parser
    process_stream_parser = process_subparsers.add_parser("stream")
    process_stream_parser.add_argument(
        "--create-topics",
        action="store_true",
        help="Pre-create Kafka topics for metrics before starting the stream processing job, if not exists",
    )

    # > Process Batch Parser
    process_batch_parser = process_subparsers.add_parser("batch")
    process_batch_parser.add_argument(
        "--topics",
        type=lambda s: [t.strip() for t in s.split(",")],
        default=None,
        help="Comma-separated list of Kafka topics to process (default: all topics)",
    )

    # > UI Parser
    ui_parser = subparsers.add_parser("ui")
    ui_subparsers = ui_parser.add_subparsers(dest="ui_command")

    # > UI Ingest Parser
    ui_ingest_parser = ui_subparsers.add_parser("ingest")
    ui_ingest_parser.add_argument(
        "--topics",
        type=lambda s: [t.strip() for t in s.split(",")],
        default=None,
        help="Comma-separated list of Kafka topics to ingest (default: all topics)",
    )

    # > UI App Parser
    ui_app_parser = ui_subparsers.add_parser("app")
    ui_app_parser.add_argument(
        "--port",
        type=int,
        default=8501,
        help="Port to run the Streamlit dashboard on",
    )
    ui_app_parser.add_argument(
        "--address",
        default="0.0.0.0",
        help="Address to bind the Streamlit dashboard to",
    )

    # Parse arguments and dispatch commands
    args = parser.parse_args()
    if args.command == "market" and args.market_command == "publish":
        publish_market_events(
            tickers=args.tickers,
            start_date=args.start_date,
            end_date=args.end_date,
            speed=args.speed,
        )
    elif args.command == "process" and args.process_command == "stream":
        process_stream(create_topics=args.create_topics)
    elif args.command == "process" and args.process_command == "batch":
        process_batch(topics=args.topics)
    elif args.command == "ui" and args.ui_command == "ingest":
        ui_ingest(topics=args.topics)
    elif args.command == "ui" and args.ui_command == "app":
        ui_app(port=args.port, address=args.address)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
