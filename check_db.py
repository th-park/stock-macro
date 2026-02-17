import pandas as pd
from app.database import SessionLocal
from app.models.stock_data import StockData

def check_db_stats():
    db = SessionLocal()
    try:
        # Check total count
        total_count = db.query(StockData).count()
        print(f"Total Records: {total_count}")
        
        if total_count > 0:
            # Check counts per ticker
            query = db.query(StockData.ticker, StockData.timestamp).statement
            df = pd.read_sql(query, db.bind)
            
            stats = df.groupby('ticker')['timestamp'].agg(['count', 'min', 'max'])
            print("\nStatistics per Ticker:")
            print(stats)
        else:
            print("Database is empty.")
            
    except Exception as e:
        print(f"Error checking DB: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    check_db_stats()
