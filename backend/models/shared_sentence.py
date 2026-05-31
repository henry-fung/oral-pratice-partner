from sqlalchemy import Column, Integer, ForeignKey, DateTime, Text, String
from sqlalchemy.orm import relationship
from datetime import datetime
from backend.database import Base


class SharedSentence(Base):
    __tablename__ = "shared_sentences"

    id = Column(Integer, primary_key=True, index=True)
    shared_scenario_id = Column(Integer, ForeignKey("shared_scenarios.id", ondelete="CASCADE"), nullable=False, index=True)
    native_text = Column(Text, nullable=False)
    target_text = Column(Text, nullable=False)
    pronunciation_guide = Column(Text)
    difficulty_level = Column(String(20), default="intermediate")
    sentence_order = Column(Integer, default=1)
    created_at = Column(DateTime, default=datetime.utcnow)

    scenario = relationship("SharedScenario", back_populates="sentences")
    progress = relationship("UserSentenceProgress", back_populates="sentence", cascade="all, delete-orphan")
