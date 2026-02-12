from app.database import init_db
from app.models.stock_data import StockData

def main():
    print("Initializing database...")
    init_db()
    print("Database initialized successfully.")

if __name__ == "__main__":
    main()
