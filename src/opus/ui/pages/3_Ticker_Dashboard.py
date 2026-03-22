from __future__ import annotations

import time
import uuid
from datetime import datetime

import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from plotly.subplots import make_subplots

from opus.ui.services.redis_connector import RedisConnector

# Page config
st.set_page_config(
    page_title="Real-Time Dashboard",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded",
)

# --- STYLES ---
st.markdown(
    """
<style>
    /* Global Styles */
    .block-container {
        padding-top: 1rem;
        padding-bottom: 2rem;
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
    
</style>
""",
    unsafe_allow_html=True,
)


class DashboardApp:
    def __init__(self):
        self.connector: RedisConnector | None = None
        self.config = {}
        self.placeholders = {}

    def setup_sidebar(self):
        with st.sidebar:
            st.title("Settings")
            
            with st.expander("Connection", expanded=True):
                self.config["host"] = st.text_input("Redis Host", "localhost")
                self.config["port"] = st.number_input("Redis Port", value=6379)
                
            with st.expander("Data Parameters", expanded=True):
                self.config["ticker"] = st.text_input("Ticker Symbol", "AAPL").upper()
                self.config["window_size"] = st.slider("Candles to Show", 20, 200, 60)
                self.config["refresh_rate"] = st.slider("Refresh Interval (s)", 0.5, 10.0, 1.0)
            
            st.markdown("---")
            self.config["running"] = st.toggle("Live Stream", value=True)
            
            st.markdown(
                """
                <div style="font-size: 0.8rem; color: #787b86; margin-top: 2rem;">
                    Status: <span style="color: #4caf50;">● Connected</span>
                </div>
                """, 
                unsafe_allow_html=True
            )

    def init_connector(self):
        try:
            self.connector = RedisConnector(
                host=self.config["host"], port=self.config["port"]
            )
            # Just instantiate for now, connection happens on first call inside connector
        except Exception as e:
            st.error(f"Could not initialize Redis Connector: {e}")
            st.stop()
        
        # We need session state to persist the config if we want to redraw without full re-run logic, 
        # but Streamlit runs top-to-bottom. We rely on st.empty() for updates.

    def setup_layout(self):
        # Header Placeholder
        self.placeholders["header"] = st.empty()
        
        # Chart Placeholder 
        self.placeholders["chart"] = st.empty()
    
    def create_chart_figure(self, df_ohlc, df_ema, ticker):
        # Create subplots: 1. Price (Main) 2. Volume (Bottom)
        fig = make_subplots(
            rows=2, cols=1, 
            shared_xaxes=True, 
            vertical_spacing=0.03, 
            subplot_titles=(None, None), 
            row_heights=[0.7, 0.3]
        )

        # 1. Candlestick Trace
        fig.add_trace(
            go.Candlestick(
                x=df_ohlc["timestamp"],
                open=df_ohlc["open"],
                high=df_ohlc["high"],
                low=df_ohlc["low"],
                close=df_ohlc["close"],
                name="OHLC",
                showlegend=False,
                increasing_line_color='#26a69a', 
                decreasing_line_color='#ef5350'
            ),
            row=1, col=1
        )

        # 2. EMA Trace
        if not df_ema.empty and "ema" in df_ema.columns:
            fig.add_trace(
                go.Scatter(
                    x=df_ema["timestamp"],
                    y=df_ema["ema"],
                    mode="lines",
                    name="EMA 9",
                    line=dict(color="#2962ff", width=2),
                    showlegend=False
                ),
                row=1, col=1
            )

        # 3. Volume Trace
        if "volume" in df_ohlc.columns:
            colors = [
                '#26a69a' if row.close >= row.open else '#ef5350' 
                for index, row in df_ohlc.iterrows()
            ]
            fig.add_trace(
                go.Bar(
                    x=df_ohlc["timestamp"],
                    y=df_ohlc["volume"],
                    name="Volume",
                    marker_color=colors,
                    showlegend=False,
                    opacity=0.5
                ),
                row=2, col=1
            )

        # Layout styling to match TradingView
        fig.update_layout(
            paper_bgcolor="#131722",
            plot_bgcolor="#131722",
            margin=dict(l=10, r=50, t=10, b=10),
            height=700,
            xaxis_rangeslider_visible=False,
            dragmode="pan",
            hovermode="x unified",
        )
        
        # X Axis styling
        fig.update_xaxes(
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
            spikethickness=1
        )
        
        # Y Axis styling (Price)
        fig.update_yaxes(
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
            row=1, col=1
        )
        
        # Y Axis styling (Volume)
        fig.update_yaxes(
            showgrid=False, 
            showticklabels=False,
            row=2, col=1
        )

        return fig

    def render_header(self, df_ohlc, df_ema, ticker):
        if df_ohlc.empty:
            self.placeholders["header"].markdown(
                f"<h3 style='color: #ef5350;'>No data for {ticker}</h3>", 
                unsafe_allow_html=True
            )
            return

        latest = df_ohlc.iloc[-1]
        close_price = latest["close"]
        
        # Calculate change
        change = 0.0
        pct_change = 0.0
        
        if len(df_ohlc) > 1:
            prev = df_ohlc.iloc[-2]
            change = close_price - prev["close"]
            if prev["close"] != 0:
                pct_change = (change / prev["close"]) * 100

        # Colors and Signs
        color = "#26a69a" if change >= 0 else "#ef5350"
        sign = "+" if change >= 0 else ""
        
        latest_vol = int(latest["volume"]) if "volume" in latest else 0
        latest_ema = df_ema.iloc[-1]["ema"] if not df_ema.empty else 0
        timestamp_str = latest["timestamp"].strftime("%H:%M:%S")

        # HTML formatting for header
        header_html = f"""
        <div class="ticker-header">
            <div class="ticker-symbol">{ticker}</div>
            <div class="current-price" style="color: {color};">
                {close_price:.2f}
            </div>
            <div class="price-change" style="background-color: {color}20; color: {color};">
                {sign}{change:.2f} ({sign}{pct_change:.2f}%)
            </div>
        </div>
        
        <div class="metrics-row">
            <div class="metric-item">Vol: <strong>{latest_vol:,}</strong></div>
            <div class="metric-item">EMA(9): <strong>{latest_ema:.2f}</strong></div>
            <div class="metric-item">High: <strong>{latest["high"]:.2f}</strong></div>
            <div class="metric-item">Low: <strong>{latest["low"]:.2f}</strong></div>
            <div style="flex-grow: 1; text-align: right; color: #787b86;">Updated: {timestamp_str}</div>
        </div>
        """
        
        self.placeholders["header"].markdown(header_html, unsafe_allow_html=True)

    def run(self):
        self.setup_sidebar()
        self.init_connector()
        self.setup_layout()

        if not self.config["running"]:
            self.placeholders["header"].info("Visualization Paused")
            # If paused, we might still show the last data, but since loop is stopped we just return 
            # or we could show last fetched data. Let's just return for simplicity.
            return

        ticker = self.config["ticker"]
        window_size = self.config["window_size"]

        # Main Loop
        chart_key_prefix = str(uuid.uuid4()) # Keep key somewhat stable or change on refresh
        
        while True:
            try:
                # 1. Fetch OHLC
                df_ohlc = self.connector.get_dataframe_ohlc(ticker, count=window_size)
                
                # 2. Fetch EMA logic
                df_ema = pd.DataFrame()
                if not df_ohlc.empty:
                    df_ema = self.connector.get_dataframe_ema(ticker, count=window_size)

                # 3. Render
                if not df_ohlc.empty:
                    self.render_header(df_ohlc, df_ema, ticker)
                    
                    fig = self.create_chart_figure(df_ohlc, df_ema, ticker)
                    
                    # Use unique key to force rerender properly but minimize flickering if possible
                    # Streamlit reruns usually handle this, but inside loop we need distinct calls 
                    # or update same placeholder.
                    
                    self.placeholders["chart"].plotly_chart(
                        fig, 
                        use_container_width=True,
                        config={'displayModeBar': False, 'scrollZoom': True},
                        key=f"chart_{chart_key_prefix}_{time.time()}" 
                    )
                else:
                    self.placeholders["header"].warning(f"Waiting for data stream for {ticker}...")
                    self.placeholders["chart"].empty()

            except Exception as e:
                print(f"Update error: {e}")
                
            time.sleep(self.config["refresh_rate"])


if __name__ == "__main__":
    app = DashboardApp()
    app.run()
