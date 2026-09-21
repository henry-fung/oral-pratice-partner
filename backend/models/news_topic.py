from datetime import datetime

from sqlalchemy import Column, Date, DateTime, Integer, String, Text, UniqueConstraint

from backend.database import Base


class NewsTopic(Base):
    """A daily news headline that can seed a topical speaking scenario."""

    __tablename__ = "news_topics"

    id = Column(Integer, primary_key=True, index=True)
    topic_date = Column(Date, nullable=False, index=True)
    headline = Column(String(500), nullable=False)
    summary = Column(Text, nullable=True)
    source_name = Column(String(200), nullable=True)
    source_url = Column(String(2000), nullable=False)
    published_at = Column(DateTime, nullable=True)
    content_language = Column(String(20), nullable=True, index=True)
    source_type = Column(String(30), nullable=False, default="news", index=True)
    content_category = Column(String(50), nullable=True)
    extracted_text = Column(Text, nullable=True)
    evidence_json = Column(Text, nullable=False, default="{}")
    extraction_status = Column(String(30), nullable=False, default="summary_only")
    fetched_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    __table_args__ = (
        UniqueConstraint("topic_date", "source_url", name="uq_news_topic_daily_source"),
    )
