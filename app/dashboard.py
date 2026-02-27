import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from app.database import SessionLocal
from app.models.stock_data import StockData
from app.config import Config
import sqlalchemy
import yfinance as yf
from plotly.subplots import make_subplots

st.set_page_config(layout="wide", page_title="Stock Data Viewer")

st.title("📈 Stock Market Data Viewer")

# Database Connection
from app.database import SessionLocal


@st.cache_data(ttl=60)
def get_tickers():
    with SessionLocal() as db:
        try:
            tickers = db.query(StockData.ticker).distinct().all()
            return [t[0] for t in tickers]
        except Exception as e:
            st.error(f"Error fetching tickers: {e}")
            return []


@st.cache_data(ttl=60)
def get_data(ticker):
    with SessionLocal() as db:
        try:
            query = db.query(StockData).filter(StockData.ticker == ticker).order_by(StockData.timestamp)
            data = pd.read_sql(query.statement, db.bind)
            return data
        except Exception as e:
            st.error(f"Error fetching data: {e}")
            return pd.DataFrame()


@st.cache_data(ttl=3600)
def get_daily_data(ticker):
    try:
        ticker_obj = yf.Ticker(ticker)
        df = ticker_obj.history(period="max", interval="1d")
        if not df.empty:
            df = df.reset_index()
            # Standardize column names to match DB format for the chart
            df = df.rename(columns={
                'Date': 'timestamp', 
                'Open': 'open', 
                'High': 'high', 
                'Low': 'low', 
                'Close': 'close', 
                'Volume': 'volume'
            })
            # Ensure timestamp has no timezone for consistency
            if df['timestamp'].dt.tz is not None:
                df['timestamp'] = df['timestamp'].dt.tz_localize(None)
            return df
        return pd.DataFrame()
    except Exception as e:
        st.error(f"Error fetching daily data: {e}")
        return pd.DataFrame()


def calculate_rsi(data, window=14):
    delta = data.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=window).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=window).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))


# Sidebar for controls
st.sidebar.header("Settings")
tickers = get_tickers()

if not tickers:
    tickers = ["AAPL", "MSFT", "GOOGL"] # Provide some fallback options if DB is empty

selected_db_ticker = st.sidebar.selectbox("Select Ticker from Database", tickers)

st.sidebar.markdown("---")
custom_ticker = st.sidebar.text_input("...or Enter Custom Ticker", placeholder="e.g., TSLA, NVDA")

# Determine which ticker to use
selected_ticker = custom_ticker.upper() if custom_ticker else selected_db_ticker

# Timeframe selection
timeframe = st.sidebar.radio("Timeframe", ["Intraday (1m, DB)", "Daily (1d, Live)"])

if selected_ticker:
        # Load Data based on timeframe
        if timeframe == "Daily (1d, Live)":
            df = get_daily_data(selected_ticker)
            title_prefix = f"Daily (Max)"
            chart_title = f'{selected_ticker} Daily Candlestick Chart (Max History)'
        else:
            df = get_data(selected_ticker)
            title_prefix = "Intraday (1m)"
            chart_title = f'{selected_ticker} Intraday Candlestick Chart'
        
        if not df.empty:
            st.subheader(f"{selected_ticker} - {title_prefix} Stock Price History")
            
            # Date Range Slider (Optional but good for large datasets)
            # st.sidebar.text("Data Points: " + str(len(df)))

            # Prepare data for categorical axis (avoid gaps)
            if timeframe == "Daily (1d, Live)":
                df['ts_str'] = df['timestamp'].apply(lambda x: x.strftime('%Y-%m-%d'))
            else:
                df['ts_str'] = df['timestamp'].apply(lambda x: x.strftime('%Y-%m-%d %H:%M:%S'))

            # Prepare Figure with Subplots (Row 1: Price, Row 2: RSI)
            fig = make_subplots(
                rows=2, cols=1, 
                shared_xaxes=True, 
                vertical_spacing=0.05, 
                row_heights=[0.7, 0.3],
                subplot_titles=(chart_title, "RSI (14)")
            )

            # CandleStick Chart (Row 1)
            fig.add_trace(go.Candlestick(
                x=df['ts_str'],
                open=df['open'],
                high=df['high'],
                low=df['low'],
                close=df['close'],
                name=selected_ticker
            ), row=1, col=1)

            # Add Moving Averages only for Daily view (Row 1)
            if timeframe == "Daily (1d, Live)":
                df['ma20'] = df['close'].rolling(window=20).mean()
                df['ma60'] = df['close'].rolling(window=60).mean()
                df['ma200'] = df['close'].rolling(window=200).mean()
                
                fig.add_trace(go.Scatter(x=df['ts_str'], y=df['ma20'], name='MA20', line=dict(color='orange', width=1.5)), row=1, col=1)
                fig.add_trace(go.Scatter(x=df['ts_str'], y=df['ma60'], name='MA60', line=dict(color='green', width=1.5)), row=1, col=1)
                fig.add_trace(go.Scatter(x=df['ts_str'], y=df['ma200'], name='MA200', line=dict(color='red', width=1.5)), row=1, col=1)

                # Add RSI (Row 2)
                df['rsi'] = calculate_rsi(df['close'])
                fig.add_trace(go.Scatter(x=df['ts_str'], y=df['rsi'], name='RSI', line=dict(color='purple', width=1.5)), row=2, col=1)
                
                # Add RSI threshold lines
                fig.add_hline(y=70, line_dash="dash", line_color="red", line_width=1, row=2, col=1)
                fig.add_hline(y=30, line_dash="dash", line_color="green", line_width=1, row=2, col=1)

            # Add vertical lines for day separation only for intraday
            if timeframe == "Intraday (1m, DB)":
                df['date_str'] = df['timestamp'].dt.strftime('%Y-%m-%d')
                unique_dates = df['date_str'].unique()
                
                for date in unique_dates[1:]:
                    first_record_of_day = df[df['date_str'] == date].iloc[0]['ts_str']
                    fig.add_vline(
                        x=first_record_of_day, 
                        line_width=1, 
                        line_dash="dash", 
                        line_color="red",
                        opacity=0.8,
                        row=1, col=1
                    )

            fig.update_layout(
                yaxis_title='Stock Price',
                yaxis2_title='RSI',
                xaxis_rangeslider_visible=False,
                height=800,
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
            )

            # Hide gaps (non-trading hours/weekends) by using category axis
            fig.update_xaxes(
                type='category',
                tickmode='auto',
                nticks=20
            )

            st.plotly_chart(fig, use_container_width=True)

            # Show raw data
            with st.expander("View Raw Data"):
                st.dataframe(df.sort_values(by='timestamp', ascending=False))
        else:
            st.warning(f"No {timeframe.split()[0].lower()} data available for **{selected_ticker}**.")
            if timeframe == "Intraday (1m, DB)":
                st.info("Intraday data requires the ticker to be tracked by the data collector and saved in the database.")
