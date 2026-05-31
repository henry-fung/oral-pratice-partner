from sqlalchemy import Column, Integer, String, DateTime, Text, UniqueConstraint
from sqlalchemy.orm import relationship
from datetime import datetime
from backend.database import Base


class SharedScenario(Base):
    __tablename__ = "shared_scenarios"

    id = Column(Integer, primary_key=True, index=True)
    role = Column(String(50), nullable=False, index=True)
    language = Column(String(20), nullable=False, index=True)
    proficiency_level = Column(String(20), nullable=False, index=True)
    title = Column(String(200), nullable=False)
    description = Column(Text)
    context = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        UniqueConstraint("role", "language", "proficiency_level", "title", name="uq_shared_scenario"),
    )

    sentences = relationship("SharedSentence", back_populates="scenario", cascade="all, delete-orphan")
    user_scenarios = relationship("UserScenario", back_populates="shared_scenario", cascade="all, delete-orphan")
