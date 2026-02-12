from sqlalchemy import Column, Integer, String, Float, DateTime, UniqueConstraint
from app.database import Base

class StockData(Base):
    __tablename__ = "stock_data"

    id = Column(Integer, primary_key=True, index=True)
    ticker = Column(String, index=True, nullable=False)
    timestamp = Column(DateTime, index=True, nullable=False)
    open = Column(Float, nullable=False)
    high = Column(Float, nullable=False)
    low = Column(Float, nullable=False)
    close = Column(Float, nullable=False)
    volume = Column(Float, nullable=False)

    # Ensure unique combination of ticker and timestamp to prevent duplicates
    __table_args__ = (
        UniqueConstraint('ticker', 'timestamp', name='uix_ticker_timestamp'),
    )

    def __repr__(self):
        return f"<StockData(ticker={self.ticker}, time={self.timestamp}, close={self.close})>"
