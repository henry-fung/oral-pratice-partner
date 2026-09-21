from datetime import datetime

from sqlalchemy import Column, Date, DateTime, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import relationship

from backend.database import Base


class NewsTopicMatch(Base):
    """Role/language-specific relevance decision for a cached source topic."""

    __tablename__ = "news_topic_matches"

    id = Column(Integer, primary_key=True, index=True)
    news_topic_id = Column(Integer, ForeignKey("news_topics.id", ondelete="CASCADE"), nullable=False, index=True)
    topic_date = Column(Date, nullable=False, index=True)
    role = Column(String(50), nullable=False, index=True)
    language = Column(String(20), nullable=False, index=True)
    interest_key = Column(String(64), nullable=False, default="", index=True)
    relevance_score = Column(Integer, nullable=False, default=0)
    diversity_group = Column(String(50), nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    topic = relationship("NewsTopic")

    __table_args__ = (
        UniqueConstraint("news_topic_id", "topic_date", "role", "language", "interest_key", name="uq_news_topic_match"),
    )
