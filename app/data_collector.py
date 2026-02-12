import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
from app.database import get_db
from app.models.stock_data import StockData
from app.config import Config
from sqlalchemy.exc import IntegrityError
import time

class DataCollector:
    def __init__(self, tickers=None):
        self.tickers = tickers if tickers else Config.TARGET_TICKERS

    def fetch_data(self, ticker, period="1mo", interval="1m"):
        """
        Fetch data from Yahoo Finance.
        Note: yfinance 1m data is limited to the last 30 days.
        To get 2 years of data, we might need to use 1h interval or a different source.
        However, enabling minute-level backtesting usually requires high-resolution data.
        For now, we fetch the maximum available 1m data (30 days) and maybe 1h for longer history.
        """
        print(f"Fetching data for {ticker} (Period: {period}, Interval: {interval})...")
        try:
            ticker_obj = yf.Ticker(ticker)
            # Fetch data
            df = ticker_obj.history(period=period, interval=interval)
            
            if df.empty:
                print(f"No data found for {ticker}")
                return []
            
            return df
        except Exception as e:
            print(f"Error fetching data for {ticker}: {e}")
            return []

    def save_to_db(self, ticker, df):
        db = next(get_db())
        data_to_insert = []
        
        for index, row in df.iterrows():
            timestamp = index.to_pydatetime()
            if timestamp.tzinfo:
                timestamp = timestamp.replace(tzinfo=None) # Make naive for simplicity in SQLite
            
            # Check if data already exists (basic check)
            # For better performance, use bulk insert with on_conflict_do_nothing
            # But here we will collect objects and try to insert them.
            # SQLAlchemy ORM doesn't support "INSERT IGNORE" easily across all DBs without specific dialect usage.
            # We will use a simple check for now or just try/except block efficiently.
            
            existing = db.query(StockData).filter_by(ticker=ticker, timestamp=timestamp).first()
            if not existing:
                stock_data = StockData(
                    ticker=ticker,
                    timestamp=timestamp,
                    open=row['Open'],
                    high=row['High'],
                    low=row['Low'],
                    close=row['Close'],
                    volume=row['Volume']
                )
                db.add(stock_data)

        try:
            db.commit()
            print(f"Committed new records for {ticker}")
        except Exception as e:
            db.rollback()
            print(f"Error committing to DB: {e}")

    def run(self):
        for ticker in self.tickers:
            # 1m data is limited to 30d max in yfinance
            df = self.fetch_data(ticker, period="1mo", interval="1m")
            if not isinstance(df, list) and not df.empty:
                self.save_to_db(ticker, df)
                
            # Optional: Fetch 2y history with 1h interval for broader backtesting context
            # df_long = self.fetch_data(ticker, period="2y", interval="1h")
            # if not isinstance(df_long, list) and not df_long.empty:
            #     self.save_to_db(ticker, df_long)

if __name__ == "__main__":
    collector = DataCollector()
    collector.run()
