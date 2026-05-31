from sqlalchemy import Column, Integer, ForeignKey, DateTime, Boolean, String, UniqueConstraint
from sqlalchemy.orm import relationship
from datetime import datetime
from backend.database import Base


class UserScenario(Base):
    __tablename__ = "user_scenarios"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    shared_scenario_id = Column(Integer, ForeignKey("shared_scenarios.id", ondelete="CASCADE"), nullable=False, index=True)
    session_id = Column(String(50), nullable=False, index=True)
    is_selected = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        UniqueConstraint("user_id", "shared_scenario_id", name="uq_user_scenario"),
    )

    shared_scenario = relationship("SharedScenario", back_populates="user_scenarios")
