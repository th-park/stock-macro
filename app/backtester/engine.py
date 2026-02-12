import backtrader as bt
import pandas as pd
from app.database import get_db
from app.models.stock_data import StockData
from app.backtester.strategy import MomentumStrategy
from app.config import Config
import datetime

def run_backtest(ticker, start_date=None, end_date=None):
    cerebro = bt.Cerebro()

    # Add Strategy
    cerebro.addstrategy(MomentumStrategy)

    # Fetch data from DB
    db = next(get_db())
    query = db.query(StockData).filter(StockData.ticker == ticker)
    
    if start_date:
        query = query.filter(StockData.timestamp >= start_date)
    if end_date:
        query = query.filter(StockData.timestamp <= end_date)
        
    data_objs = query.order_by(StockData.timestamp).all()
    
    if not data_objs:
        print(f"No data found for {ticker}")
        return

    # Convert to Pandas DataFrame
    data_list = [
        {
            'datetime': d.timestamp,
            'open': d.open,
            'high': d.high,
            'low': d.low,
            'close': d.close,
            'volume': d.volume
        }
        for d in data_objs
    ]
    df = pd.DataFrame(data_list)
    df.set_index('datetime', inplace=True)

    # Create Data Feed
    data = bt.feeds.PandasData(dataname=df)

    cerebro.adddata(data)

    # Set our desired cash start
    cerebro.broker.setcash(Config.INITIAL_CAPITAL)

    # Set the commission - 0.1% ... divide by 100 to remove the %
    cerebro.broker.setcommission(commission=0.001)

    print(f'Starting Portfolio Value: {cerebro.broker.getvalue():.2f}')

    cerebro.run()

    print(f'Final Portfolio Value: {cerebro.broker.getvalue():.2f}')
    
    # Plotting
    # cerebro.plot() # Requires matplotlib, might not work in headless env without tweaks

if __name__ == "__main__":
    # Example usage
    target_ticker = Config.TARGET_TICKERS[0]
    print(f"Running backtest for {target_ticker}")
    run_backtest(target_ticker)
