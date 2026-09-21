from datetime import datetime

from sqlalchemy import Boolean, Column, Date, DateTime, Integer

from backend.database import Base


class NewsFetchLog(Base):
    """Records a daily feed attempt so an outage does not trigger request storms."""

    __tablename__ = "news_fetch_logs"

    id = Column(Integer, primary_key=True, index=True)
    topic_date = Column(Date, nullable=False, unique=True, index=True)
    successful = Column(Boolean, nullable=False)
    fetched_at = Column(DateTime, nullable=False, default=datetime.utcnow)
