import json
import logging
import os
from datetime import datetime
from typing import Any, List, Optional

import redis

logger = logging.getLogger(__name__)


class RedisStorage:
    def __init__(
        self,
        host: str = "localhost",
        port: int = 6379,
        db: int = 0,
        socket_timeout: int = 5,
    ):
        # Allow env override
        host = os.getenv("REDIS_HOST", host)
        port = int(os.getenv("REDIS_PORT", str(port)))
        self.client = redis.Redis(
            host=host, port=port, db=db, decode_responses=True, socket_timeout=socket_timeout
        )

    def _get_timestamp_score(self, iso_ts: str) -> float:
        try:
            dt = datetime.fromisoformat(iso_ts.replace("Z", "+00:00"))
            return dt.timestamp()
        except (ValueError, TypeError):
            return 0.0

    def push_records(self, key_prefix: str, records: List[dict[str, Any]], score_key: str) -> int:
        """
        Pushes a batch of records to a Redis Sorted Set.
        Key schema: {key_prefix}:{ticker}
        Score: Timestamp from record[score_key]
        Value: JSON string of record
        """
        count = 0
        pipeline = self.client.pipeline()
        for record in records:
            ticker = record.get("ticker")
            if not ticker:
                continue
            
            ts_val = record.get(score_key)
            if not ts_val:
                continue

            score = self._get_timestamp_score(ts_val)
            if score == 0.0:
                continue

            # Store the whole record as JSON
            member = json.dumps(record, sort_keys=True)
            redis_key = f"{key_prefix}:{ticker}"
            pipeline.zadd(redis_key, {member: score})
            count += 1
        
        pipeline.execute()
        return count

    def get_records(self, key_prefix: str, ticker: str, start_ts: float = 0, end_ts: float = float("inf"), limit: int = 500) -> List[dict[str, Any]]:
        """
        Fetch records from Redis Sorted Set by score range.
        Defaults to fetching the latest 'limit' records if range is wide.
        """
        redis_key = f"{key_prefix}:{ticker}"
        # We generally want the latest data, so we might want to use zrevrange
        # But for plotting we want chronological order.
        
        # If specific range requested:
        if start_ts > 0 or end_ts != float("inf"):
            results = self.client.zrangebyscore(redis_key, min=start_ts, max=end_ts)
        else:
            # Get last N records
            results = self.client.zrange(redis_key, start=-limit, end=-1)

        parsed = []
        for r in results:
            try:
                parsed.append(json.loads(r))
            except json.JSONDecodeError:
                continue
        return parsed

    def get_available_tickers(self) -> List[str]:
        # Fetch from the tickers set
        tickers = self.client.smembers("tickers")
        if not tickers:
             # Fallback: scan if set is empty (migration)
            keys = self.client.keys("ohlc:*")
            tickers = {k.split(":")[-1] for k in keys}
        return sorted(list(tickers))

    def register_ticker(self, ticker: str):
        self.client.sadd("tickers", ticker)

    def clear(self):
        self.client.flushdb()
