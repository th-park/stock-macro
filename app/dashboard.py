import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from app.database import SessionLocal
from app.models.stock_data import StockData
from app.config import Config
import sqlalchemy

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

            # Prepare data for categorical axis (avoid gaps)
            df['ts_str'] = df['timestamp'].apply(lambda x: x.strftime('%Y-%m-%d %H:%M:%S'))

            # CandleStick Chart
            fig = go.Figure(data=[go.Candlestick(
                x=df['ts_str'],
                open=df['open'],
                high=df['high'],
                low=df['low'],
                close=df['close'],
                name=selected_ticker
            )])

            # Add vertical lines for day separation
            # Since x-axis is categorical, x values are effectively indices (0, 1, 2, ...)
            # We need to find the indices where the date changes
            df['date_str'] = df['timestamp'].dt.strftime('%Y-%m-%d')
            unique_dates = df['date_str'].unique()
            
            # Find the indices where the date changes
            # We iterate through dates and find the first index of each new date (except the first one)
            for date in unique_dates[1:]:
                # Find the first occurrence of this date
                idx = df[df['date_str'] == date].index[0]
                # In a categorical axis with pandas dataframe source, plotly uses the value itself or index. 
                # When type='category', plotly maps x values to integers 0, 1, 2... based on their order.
                # If we passed the column directly, plotly uses the values.
                # To place a line *between* days, we might simply use the timestamp value of the first record of the new day.
                
                first_record_of_day = df[df['date_str'] == date].iloc[0]['ts_str']
                
                fig.add_vline(
                    x=first_record_of_day, 
                    line_width=1, 
                    line_dash="dash", 
                    line_color="red",
                    opacity=0.8
                )

            fig.update_layout(
                title=f'{selected_ticker} Candlestick Chart',
                yaxis_title='Stock Price',
                xaxis_title='Date',
                xaxis_rangeslider_visible=False,
                height=600
            )

            # Hide gaps (non-trading hours/weekends) by using category axis
            # We format the tick labels to ensure they are readable
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
            st.info("No data available for this ticker.")
