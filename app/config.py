import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # Database
    DB_PATH = os.getenv("DB_PATH", "sqlite:///stock_data.db")
    
    # Mirae Asset API
    MIRAE_API_KEY = os.getenv("MIRAE_API_KEY", "")
    MIRAE_SECRET_KEY = os.getenv("MIRAE_SECRET_KEY", "")
    MIRAE_ACCOUNT_NO = os.getenv("MIRAE_ACCOUNT_NO", "")
    
    # Data Collection
    TARGET_TICKERS = ["AAPL", "TSLA", "NVDA", "SPY", "QQQ", "TQQQ", "SOXL"] # Default tickers
    DATA_START_DATE = "2022-01-01" # Approx 2 years ago, will be calculated dynamically
    
    # Backtest
    INITIAL_CAPITAL = 10000.0
