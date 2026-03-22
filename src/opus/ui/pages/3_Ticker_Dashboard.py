from __future__ import annotations

import time
import uuid

import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from plotly.subplots import make_subplots

from opus.ui.services.redis_connector import RedisConnector

st.set_page_config(
    page_title="Ticker Real-Time Dashboard",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded",
)

# =================================================
# Markdown Styles
# =================================================
st.markdown(
    """
<style>
    /* Global Styles */
    .block-container {
        padding-top: 3rem !important;
        padding-bottom: 2rem;
        padding-left: 2rem !important;
        padding-right: 2rem !important;
    }
    
    /* Dark Theme Background */
    .stApp {
        background-color: #131722;
        color: #d1d4dc;
    }
    
    /* Sidebar */
    [data-testid="stSidebar"] {
        background-color: #1e222d;
        border-right: 1px solid #2a2e39;
    }
    
    /* Header Container */
    .ticker-header {
        display: flex;
        align-items: center;
        margin-bottom: 1rem;
        padding: 0.5rem 0;
        border-bottom: 1px solid #2a2e39;
    }
    
    .ticker-symbol {
        font-size: 2rem;
        font-weight: 700;
        margin-right: 1rem;
        color: #ffffff;
    }
    
    .current-price {
        font-size: 2rem;
        font-weight: 600;
        /* Color set dynamically in python */
        margin-right: 1rem;
    }
    
    .price-change {
        font-size: 1.2rem;
        font-weight: 500;
        padding: 0.2rem 0.5rem;
        border-radius: 4px;
    }
    
    .metrics-row {
        display: flex;
        gap: 2rem;
        font-size: 0.9rem;
        color: #787b86;
        margin-bottom: 0.5rem;
    }
    
    .metric-item strong {
        color: #d1d4dc;
        margin-left: 0.3rem;
    }

    /* Inputs */
    .stTextInput > div > div > input {
        color: #d1d4dc;
        background-color: #2a2e39;
        border: 1px solid #434651;
    }
    
    /* Buttons */
    .stButton > button {
        background-color: #2962ff;
        color: white;
        border: none;
        width: 100%;
    }
    
    .stButton > button:hover {
        background-color: #1e53e5;
    }

    /* Plotly Chart Container */
    .js-plotly-plot .plotly .modebar {
        left: 50%;
        transform: translateX(-50%);
    }
    
    /* Status indicator styling */
    .status-connected {
        color: #26a69a;
    }
    
    .status-disconnected {
        color: #ef5350;
    }
    
    /* Custom scrollbar */
    ::-webkit-scrollbar {
        width: 8px;
        height: 8px;
    }
    
    ::-webkit-scrollbar-track {
        background: #131722;
    }
    
    ::-webkit-scrollbar-thumb {
        background: #2a2e39;
        border-radius: 4px;
    }
    
    ::-webkit-scrollbar-thumb:hover {
        background: #434651;
    }
</style>
""",
    unsafe_allow_html=True,
)


class TickerDashboard:
    def __init__(self):
        self.connector: RedisConnector | None = None
        self.config = {}
        # Generate a unique key for this session
        self.session_key = {uuid.uuid4().hex[:8]}

    def initialize_connector(self):
        # Redis connection setup
        if "connector" not in st.session_state:
            try:
                st.session_state["connector"] = RedisConnector(
                    host=self.config["redis_host"],
                    port=self.config["redis_port"],
                )
            except Exception as err:
                st.error(f"Could not initialize the Redis Connector: {err}")
                st.stop()
        self.connector = st.session_state["connector"]

        # Ensure config matches current session state (if host/port changed)
        if (
            self.connector.host != self.config["redis_host"]
            or self.connector.port != self.config["redis_port"]
        ):
            try:
                self.connector = RedisConnector(
                    host=self.config["redis_host"],
                    port=self.config["redis_port"],
                )
                st.session_state["connector"] = self.connector
            except Exception as err:
                st.error(f"Could not update the Redis Connector: {err}")

    def build_sidebar(self):
        with st.sidebar:
            st.title("⚙️ Settings")

            with st.expander("Connection Parameters 🔌", expanded=True):
                self.config["redis_host"] = st.text_input("Redis Host", "localhost")
                self.config["redis_port"] = st.number_input("Redis Port", value=6379)

            with st.expander("Data Parameters 📊", expanded=True):
                self.config["ticker"] = st.text_input("Ticker Symbol", "AAPL").upper()
                self.config["window_size"] = st.slider("Candles to Show", 20, 200, 60)
                self.config["refresh_rate"] = st.slider(
                    "Refresh Interval (s)",
                    0.5,
                    10.0,
                    1.0,
                )
            st.markdown("---")
            self.config["live"] = st.toggle("🔴 Live Stream", value=True)
            st.markdown("---")

            # Status indicator
            status_color = (
                "status-connected" if self.config.get("live") else "status-disconnected"
            )
            status_text = "Streaming ●" if self.config.get("live") else "Paused ●"
            status_html = f"""
            <div style="font-size: 0.85rem; margin-top: 1rem;">
                Status: <span class="{status_color}">{status_text}</span>
            </div>
            """
            st.markdown(status_html, unsafe_allow_html=True)

    def build_header(
        self,
        ticker: str,
        dataframe_ohlc: pd.DataFrame,
        dataframe_ema: pd.DataFrame,
    ):
        if dataframe_ohlc.empty:
            st.markdown(
                f"""
                <div style="margin-top: 2rem;">
                    <h3 style="color: #ef5350;">📊 No data available for ticker `{ticker}`</h3>
                    <p style="color: #787b86;">Waiting for data stream to arrive...</p>
                </div>
                """,
                unsafe_allow_html=True,
            )
            return

        latest_candlestick = dataframe_ohlc.iloc[-1]
        latest_close_price = latest_candlestick["close"]

        # Calculate change
        latest_change = 0.0
        latest_percent_change = 0.0

        if len(dataframe_ohlc) > 1:
            prev = dataframe_ohlc.iloc[-2]
            latest_change = latest_close_price - prev["close"]
            if prev["close"] != 0:
                latest_percent_change = (latest_change / prev["close"]) * 100

        # Calculate colors and signs
        color = "#26a69a" if latest_change >= 0 else "#ef5350"
        sign = "+" if latest_change >= 0 else ""
        arrow = "▲" if latest_change >= 0 else "▼"

        latest_volume = (
            int(latest_candlestick["volume"]) if "volume" in latest_candlestick else 0
        )
        latest_ema = dataframe_ema.iloc[-1]["ema"] if not dataframe_ema.empty else 0
        latest_timestamp = latest_candlestick["timestamp"].strftime("%H:%M:%S")

        # HTML formatting for header
        header_html = f"""
        <div class="ticker-header">
            <div class="ticker-symbol">{ticker}</div>
            <div class="current-price" style="color: {color};">
                {latest_close_price:.2f}
            </div>
            <div class="price-change" style="background-color: {color}20; color: {color};">
                {arrow} {sign}{latest_change:.2f} ({sign}{latest_percent_change:.2f}%)
            </div>
        </div>
        
        <div class="metrics-row">
            <div class="metric-item">📊 Vol: <strong>{latest_volume:,}</strong></div>
            <div class="metric-item">📈 EMA(9): <strong>{latest_ema:.2f}</strong></div>
            <div class="metric-item">⬆️ High: <strong>{latest_candlestick["high"]:.2f}</strong></div>
            <div class="metric-item">⬇️ Low: <strong>{latest_candlestick["low"]:.2f}</strong></div>
            <div style="flex-grow: 1; text-align: right; color: #787b86;">🕐 {latest_timestamp}</div>
        </div>
        """

        st.markdown(header_html, unsafe_allow_html=True)

    def build_chart_figure(
        self,
        dataframe_ohlc: pd.DataFrame,
        dataframe_ema: pd.DataFrame,
        *,
        name_ohlc: str = "Candlestick (5m)",
        name_ema: str = "EMA 9",
    ):
        # Create subplots: 1. Price (Main) 2. Volume (Bottom)
        figure = make_subplots(
            rows=2,
            cols=1,
            shared_xaxes=True,
            vertical_spacing=0.03,
            subplot_titles=(None, None),
            row_heights=[0.7, 0.3],
        )

        # 1. Candlestick Trace
        figure.add_trace(
            go.Candlestick(
                x=dataframe_ohlc["timestamp"],
                open=dataframe_ohlc["open"],
                high=dataframe_ohlc["high"],
                low=dataframe_ohlc["low"],
                close=dataframe_ohlc["close"],
                name=name_ohlc,
                showlegend=False,
                increasing_line_color="#26a69a",
                decreasing_line_color="#ef5350",
            ),
            row=1,
            col=1,
        )

        # 2. EMA Trace
        if not dataframe_ema.empty:
            figure.add_trace(
                go.Scatter(
                    x=dataframe_ema["timestamp"],
                    y=dataframe_ema["ema"],
                    mode="lines",
                    name=name_ema,
                    line=dict(color="#fffc33", width=3),
                    showlegend=False,
                ),
                row=1,
                col=1,
            )

        # 3. Volume Trace
        if "volume" in dataframe_ohlc.columns:
            colors = [
                "#26a69a" if row.close >= row.open else "#ef5350"
                for index, row in dataframe_ohlc.iterrows()
            ]
            figure.add_trace(
                go.Bar(
                    x=dataframe_ohlc["timestamp"],
                    y=dataframe_ohlc["volume"],
                    name="Volume",
                    marker_color=colors,
                    showlegend=False,
                    opacity=0.5,
                ),
                row=2,
                col=1,
            )

        # Layout styling to match TradingView
        figure.update_layout(
            paper_bgcolor="#131722",
            plot_bgcolor="#131722",
            margin=dict(l=10, r=50, t=10, b=10),
            height=600,
            xaxis_rangeslider_visible=False,
            dragmode="pan",
            hovermode="x unified",
        )

        # X Axis styling
        figure.update_xaxes(
            showgrid=True,
            gridcolor="#2a2e39",
            gridwidth=1,
            zeroline=False,
            showspikes=True,
            spikemode="across",
            spikesnap="cursor",
            showline=False,
            spikedash="dash",
            spikecolor="#787b86",
            spikethickness=1,
        )

        # Y Axis styling (Price)
        figure.update_yaxes(
            showgrid=True,
            gridcolor="#2a2e39",
            gridwidth=1,
            zeroline=False,
            showspikes=True,
            spikemode="across",
            spikesnap="cursor",
            showline=False,
            spikedash="dash",
            spikecolor="#787b86",
            spikethickness=1,
            side="right",
            row=1,
            col=1,
        )

        # Y Axis styling (Volume)
        figure.update_yaxes(showgrid=False, showticklabels=False, row=2, col=1)

        return figure

    def build_chart(self):
        """Build the chart:
        Live and paused states use the same rendering logic, but with different keys to avoid Streamlit caching issues.
        """

        ticker = self.config["ticker"]
        window_size = self.config["window_size"]
        try:
            # Fetch data
            dataframe_ohlc = self.connector.get_dataframe_ohlc(
                ticker, count=window_size
            )
            dataframe_ema = pd.DataFrame()
            if not dataframe_ohlc.empty:
                dataframe_ema = self.connector.get_dataframe_ema(
                    ticker, count=window_size
                )

            if not dataframe_ohlc.empty:
                self.build_header(ticker, dataframe_ohlc, dataframe_ema)

                figure = self.build_chart_figure(dataframe_ohlc, dataframe_ema)

                # Use unique key with session-based prefix to avoid duplicates
                suffix = "live" if self.config["live"] else "paused"
                st.plotly_chart(
                    figure,
                    width="stretch",
                    config={"displayModeBar": False, "scrollZoom": True},
                    key=f"{self.session_key}_{suffix}",
                )

                # Only show paused message when live stream is OFF
                if not self.config["live"]:
                    st.info(
                        "Live stream paused ⏸️ Toggle 'Live Stream' to resume updates."
                    )
                else:
                    st.info(
                        "Live stream active 📈 Toggle 'Live Stream' to pause updates."
                    )
            else:
                st.warning(f"📊 Waiting for ticker data stream '{ticker}' ...")

        except Exception as err:
            st.error(f"Could not build chart: {err}")

    def render(self):
        self.build_sidebar()
        self.initialize_connector()

        # Render chart (works for both live and paused states)
        self.build_chart()

        # Schedule next update only if running
        if self.config["live"]:
            time.sleep(self.config["refresh_rate"])
            st.rerun()


dashboard = TickerDashboard()
dashboard.render()
