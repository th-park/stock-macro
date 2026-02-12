import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from app.database import get_db
from app.models.stock_data import StockData
from app.config import Config
import sqlalchemy

st.set_page_config(layout="wide", page_title="Stock Data Viewer")

st.title("📈 Stock Market Data Viewer")

# Database Connection
db = next(get_db())

@st.cache_data(ttl=60)
def get_tickers():
    try:
        tickers = db.query(StockData.ticker).distinct().all()
        return [t[0] for t in tickers]
    except Exception as e:
        st.error(f"Error fetching tickers: {e}")
        return []

@st.cache_data(ttl=60)
def get_data(ticker):
    try:
        query = db.query(StockData).filter(StockData.ticker == ticker).order_by(StockData.timestamp)
        data = pd.read_sql(query.statement, db.bind)
        return data
    except Exception as e:
        st.error(f"Error fetching data: {e}")
        return pd.DataFrame()

# Sidebar for controls
st.sidebar.header("Settings")
tickers = get_tickers()
if not tickers:
    st.warning("No data found in database. Please run the data collector first.")
else:
    selected_ticker = st.sidebar.selectbox("Select Ticker", tickers)
    
    if selected_ticker:
        # Load Data
        df = get_data(selected_ticker)
        
        if not df.empty:
            st.subheader(f"{selected_ticker} - Stock Price History")
            
            # Date Range Slider (Optional but good for large datasets)
            # st.sidebar.text("Data Points: " + str(len(df)))

            # CandleStick Chart
            fig = go.Figure(data=[go.Candlestick(
                x=df['timestamp'],
                open=df['open'],
                high=df['high'],
                low=df['low'],
                close=df['close'],
                name=selected_ticker
            )])

            fig.update_layout(
                title=f'{selected_ticker} Candlestick Chart',
                yaxis_title='Stock Price',
                xaxis_title='Date',
                xaxis_rangeslider_visible=False,
                height=600
            )

            st.plotly_chart(fig, use_container_width=True)

            # Show raw data
            with st.expander("View Raw Data"):
                st.dataframe(df.sort_values(by='timestamp', ascending=False))
        else:
            st.info("No data available for this ticker.")
