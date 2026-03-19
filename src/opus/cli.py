import argparse
import asyncio

from opus.market.publisher import publish_market_events
from opus.process.stream.flink_job import process_stream


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
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
