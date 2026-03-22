from __future__ import annotations

import logging

import pandas as pd
import redis

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class RedisConnector:
    def __init__(self, host: str, port: int):
        self.host = host
        self.port = port
        self.client: redis.Redis | None = None

    def connect(self):
        """Initializes the Redis connection."""

        if self.client is None:
            try:
                self.client = redis.Redis(
                    host=self.host,
                    port=self.port,
                    decode_responses=True,
                )
                self.client.ping()
            except redis.ConnectionError as err:
                # Re-raise or handle, for now we let the caller handle it or we use st.error if we were in UI code
                # typically services shouldn't know about 'st', but for simplicity we might just raise
                raise ConnectionError(
                    f"Unable to connect to Redis at {self.host}:{self.port}"
                ) from err

    def _as_dataframe_ohlc(self, dataframe: pd.DataFrame) -> pd.DataFrame:
        """Clean and format the OHLC DataFrame."""
        if dataframe.empty:
            return dataframe

        columns = ["open", "high", "low", "close", "volume"]
        for column in [column for column in columns if column in dataframe.columns]:
            dataframe[column] = pd.to_numeric(dataframe[column], errors="coerce")

        # Convert timestamp
        if "end" in dataframe.columns:
            dataframe["timestamp"] = pd.to_datetime(dataframe["end"])

        # Sort by timestamp i.e. oldest first for plotting
        return dataframe.sort_values("timestamp")

    def _as_dataframe_ema(self, dataframe: pd.DataFrame) -> pd.DataFrame:
        """Clean and format the EMA DataFrame."""
        if dataframe.empty:
            return dataframe

        if "ema" in dataframe.columns:
            dataframe["ema"] = pd.to_numeric(dataframe["ema"], errors="coerce")

        if "time" in dataframe.columns:
            try:
                # Try assuming milliseconds first if numeric-ish
                dataframe["timestamp"] = pd.to_datetime(dataframe["time"], unit="ms")
            except Exception:
                # Otherwise, fallback to standard parsing
                dataframe["timestamp"] = pd.to_datetime(dataframe["time"])

        # Sort by timestamp i.e. oldest first for plotting
        return dataframe.sort_values("timestamp")

    def get_dataframe_ohlc(
        self,
        ticker: str,
        count: int | None = None,
    ) -> pd.DataFrame:
        """Get latest OHLC dataframe for a particular ticker."""
        if not self.client:
            self.connect()

        stream_key = f"OHLC_5M:{ticker}"
        try:
            # xrevrange returns the data in reversed chronological order (i.e. newest first)
            dataset = self.client.xrevrange(stream_key, count=count)
            if not dataset:
                return pd.DataFrame()

            dataset_parsed = []
            for redis_id, values in dataset:
                values["id"] = redis_id
                dataset_parsed.append(values)

            dataframe = pd.DataFrame(dataset_parsed)
            return self._as_dataframe_ohlc(dataframe)

        except Exception as err:
            logger.info(f"Failed to get OHLC dataframe: {err}")
            return pd.DataFrame()

    def get_dataframe_ema(
        self,
        ticker: str,
        count: int | None = None,
    ) -> pd.DataFrame:
        """Get latest EMA dataframe for a particular ticker."""
        if not self.client:
            self.connect()

        stream_key = f"OHLC_5M_EMA_9:{ticker}"
        try:
            # xrevrange returns the data in reversed chronological order (i.e. newest first)
            dataset = self.client.xrevrange(stream_key, count=count)
            if not dataset:
                return pd.DataFrame()

            dataset_parsed = []
            for redis_id, values in dataset:
                values["id"] = redis_id
                dataset_parsed.append(values)

            dataframe = pd.DataFrame(dataset_parsed)
            return self._as_dataframe_ema(dataframe)

        except Exception as err:
            logger.info(f"Failed to fetch EMA dataframe: {err}")
            return pd.DataFrame()

    def get_dataframe_ema_range(
        self,
        ticker: str,
        min_id: int | str = "-",
        max_id: int | str = "+",
        count: int = None,
    ) -> pd.DataFrame:
        """Get EMA dataframe for a particular ticker within a specific ID range."""
        if not self.client:
            self.connect()

        stream_key = f"OHLC_5M_EMA_9:{ticker}"
        try:
            # xrange returns the data in chronological order (i.e. oldest first)
            dataset = self.client.xrange(
                stream_key, min=min_id, max=max_id, count=count
            )
            if not dataset:
                return pd.DataFrame()

            dataset_parsed = []
            for redis_id, values in dataset:
                values["id"] = redis_id
                dataset_parsed.append(values)

            dataframe = pd.DataFrame(dataset_parsed)
            return self._as_dataframe_ema(dataframe)

        except Exception as err:
            logger.info(f"Failed to fetch EMA-range dataframe: {err}")
            return pd.DataFrame()
