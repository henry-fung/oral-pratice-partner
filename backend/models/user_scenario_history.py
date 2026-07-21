from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, Integer, UniqueConstraint

from backend.database import Base


class UserScenarioHistory(Base):
    """Durable record of AI-generated scenarios that a user has already seen."""

    __tablename__ = "user_scenario_history"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    shared_scenario_id = Column(
        Integer,
        ForeignKey("shared_scenarios.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    last_seen_at = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)

    __table_args__ = (
        UniqueConstraint("user_id", "shared_scenario_id", name="uq_user_scenario_history"),
    )
