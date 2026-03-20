from __future__ import annotations

import json
import logging
import subprocess
import sys
import time
from datetime import datetime
from typing import Any

import plotly.graph_objects as go
import streamlit as st

try:
    from .constants import (
        DEFAULT_STREAMLIT_PORT,
        KAFKA_BOOTSTRAP_SERVERS,
    )
    from .storage import RedisStorage
except ImportError:
    from opus.ui.constants import (
        DEFAULT_STREAMLIT_PORT,
        KAFKA_BOOTSTRAP_SERVERS,
    )
    from opus.ui.storage import RedisStorage

logger = logging.getLogger(__name__)


def _parse_iso_timestamp(value: Any) -> datetime | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        return value

    raw = str(value).strip()
    if not raw:
        return None

    try:
        return datetime.fromisoformat(raw.replace("Z", "+00:00"))
    except ValueError:
        return None


def _decode_json_payload(
    payload: bytes | str | dict[str, Any] | None,
) -> dict[str, Any] | None:
    if payload is None:
        return None
    if isinstance(payload, dict):
        return payload

    try:
        text = (
            payload.decode("utf-8")
            if isinstance(payload, (bytes, bytearray))
            else str(payload)
        )
        decoded = json.loads(text)
        return decoded if isinstance(decoded, dict) else None
    except (UnicodeDecodeError, json.JSONDecodeError, TypeError):
        return None


def get_redis_store() -> RedisStorage:
    # Use streamlit cache_resource to reuse connection
    if "redis_store" not in st.session_state:
        st.session_state.redis_store = RedisStorage(host="127.0.0.1", port=6379)
    return st.session_state.redis_store


def build_single_ticker_series(
    ohlc_rows: list[dict[str, Any]],
    ema9_rows: list[dict[str, Any]],
    ema12_rows: list[dict[str, Any]],
    *,
    ticker: str,
    max_points: int,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    candles: list[dict[str, Any]] = []
    ema9: list[dict[str, Any]] = []
    ema12: list[dict[str, Any]] = []

    for row in ohlc_rows:
        if row.get("ticker") != ticker:
            continue

        ts = _parse_iso_timestamp(row.get("window_end"))
        if ts is None:
            continue

        open_price = row.get("open_price")
        high_price = row.get("high_price")
        low_price = row.get("low_price")
        close_price = row.get("close_price")
        if (
            open_price is None
            or high_price is None
            or low_price is None
            or close_price is None
        ):
            continue

        try:
            open_price = float(open_price)
            high_price = float(high_price)
            low_price = float(low_price)
            close_price = float(close_price)
        except (TypeError, ValueError):
            continue

        candles.append(
            {
                "timestamp": ts,
                "open": open_price,
                "high": high_price,
                "low": low_price,
                "close": close_price,
            }
        )

    for row in ema9_rows:
        if row.get("ticker") != ticker:
            continue
        ts = _parse_iso_timestamp(row.get("snapshot_time"))
        value = row.get("ema_value")
        if ts is None or value is None:
            continue
        try:
            value = float(value)
        except (TypeError, ValueError):
            continue
        ema9.append({"timestamp": ts, "value": value})

    for row in ema12_rows:
        if row.get("ticker") != ticker:
            continue
        ts = _parse_iso_timestamp(row.get("snapshot_time"))
        value = row.get("ema_value")
        if ts is None or value is None:
            continue
        try:
            value = float(value)
        except (TypeError, ValueError):
            continue
        ema12.append({"timestamp": ts, "value": value})

    candles = sorted(candles, key=lambda item: item["timestamp"])[-max_points:]
    ema9 = sorted(ema9, key=lambda item: item["timestamp"])
    ema12 = sorted(ema12, key=lambda item: item["timestamp"])

    # Keep EMA overlays in the same time window as the displayed candles.
    # OHLC and EMA topics have very different event densities, so slicing both by
    # row count alone can visually desynchronize them.
    if candles:
        min_ts = candles[0]["timestamp"]
        max_ts = candles[-1]["timestamp"]
        ema9 = [p for p in ema9 if min_ts <= p["timestamp"] <= max_ts]
        ema12 = [p for p in ema12 if min_ts <= p["timestamp"] <= max_ts]

    ema9 = ema9[-max_points:]
    ema12 = ema12[-max_points:]
    return candles, ema9, ema12


def _render_ticker_chart(
    ticker: str,
    candles: list[dict[str, Any]],
    ema9_points: list[dict[str, Any]],
    ema12_points: list[dict[str, Any]],
) -> None:
    candle_x = [p["timestamp"] for p in candles]

    figure = go.Figure()
    figure.add_trace(
        go.Candlestick(
            x=candle_x,
            open=[p["open"] for p in candles],
            high=[p["high"] for p in candles],
            low=[p["low"] for p in candles],
            close=[p["close"] for p in candles],
            name="OHLC",
            increasing_line_color="#0f766e",
            decreasing_line_color="#dc2626",
            yaxis="y",
        )
    )
    figure.add_trace(
        go.Scatter(
            x=[p["timestamp"] for p in ema9_points],
            y=[p["value"] for p in ema9_points],
            mode="lines",
            name="EMA9",
            line={"width": 1.7, "color": "#f59e0b"},
            yaxis="y",
        )
    )
    figure.add_trace(
        go.Scatter(
            x=[p["timestamp"] for p in ema12_points],
            y=[p["value"] for p in ema12_points],
            mode="lines",
            name="EMA12",
            line={"width": 1.7, "color": "#7c3aed"},
            yaxis="y",
        )
    )

    scale_values = [p["high"] for p in candles] + [p["low"] for p in candles]
    scale_values.extend(p["value"] for p in ema9_points)
    scale_values.extend(p["value"] for p in ema12_points)

    y_axis_config: dict[str, Any] = {}
    if scale_values:
        y_min = min(scale_values)
        y_max = max(scale_values)
        padding = (y_max - y_min) * 0.02 if y_max > y_min else max(y_max * 0.01, 1e-6)
        y_axis_config = {"range": [y_min - padding, y_max + padding]}

    figure.update_layout(
        title=f"{ticker} Candlestick + EMA",
        xaxis_title="Timestamp",
        yaxis_title="Value",
        yaxis=y_axis_config,
        legend={"orientation": "h", "y": 1.02, "x": 0},
        margin={"l": 10, "r": 10, "t": 40, "b": 10},
        template="plotly_white",
        xaxis_rangeslider_visible=False,
    )

    st.plotly_chart(figure, width="stretch")


def main() -> None:
    st.set_page_config(page_title="Opus UI", layout="wide")
    st.title("Opus Real-Time Dashboard")
    st.caption(
        "Redis-backed live view of 5-minute ticker candlesticks, EMA-9, and EMA-12."
    )

    # Initialize redis connection
    try:
        store = get_redis_store()
    except Exception as e:
        st.error(f"Could not connect to Redis: {e}")
        return

    st.sidebar.header("Controls")

    tickers = store.get_available_tickers()
    if not tickers:
        st.warning("No tickers found in Redis. Ensure ingest service is running.")
        if st.button("Refresh Tickers"):
            st.rerun()
        return

    selected_ticker = st.sidebar.selectbox(
        "Ticker",
        options=tickers,
        index=0,
        help="Select ticker to view.",
    )

    max_points = st.sidebar.slider("Chart points", 20, 500, 120, 10)
    auto_refresh = st.sidebar.checkbox("Auto-refresh", value=True)
    refresh_interval_seconds = st.sidebar.slider(
        "Refresh interval (sec)",
        1,
        30,
        2,
        1,
    )

    if st.sidebar.button("Refresh Now"):
        st.rerun()

    # Fetch data directly from Redis
    ohlc_rows = store.get_records("ohlc", selected_ticker, limit=max_points)
    ema9_rows = store.get_records("ema9", selected_ticker, limit=max_points)
    ema12_rows = store.get_records("ema12", selected_ticker, limit=max_points)

    candles, ema9_points, ema12_points = build_single_ticker_series(
        ohlc_rows,
        ema9_rows,
        ema12_rows,
        ticker=selected_ticker,
        max_points=max_points,
    )

    if not candles:
        st.info(f"No chartable points yet for {selected_ticker}.")
    else:
        _render_ticker_chart(selected_ticker, candles, ema9_points, ema12_points)

        # Display latest quote
        latest = candles[-1]
        st.metric(
            label=f"{selected_ticker} Price",
            value=f"${latest['close']:.2f}",
            delta=f"{latest['close'] - latest['open']:.2f}",
        )

    if auto_refresh:
        time.sleep(refresh_interval_seconds)
        st.rerun()


def ui_app(
    *,
    address: str = "0.0.0.0",
    port: int = DEFAULT_STREAMLIT_PORT,
) -> None:
    subprocess.run(
        [
            sys.executable,
            "-m",
            "streamlit",
            "run",
            __file__,
            "--server.port",
            str(port),
            "--server.address",
            address,
        ],
        check=True,
    )


if __name__ == "__main__":
    main()
