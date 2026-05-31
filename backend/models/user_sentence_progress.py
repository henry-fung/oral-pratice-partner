from sqlalchemy import Column, Integer, ForeignKey, DateTime, Text, Boolean, UniqueConstraint
from sqlalchemy.orm import relationship
from datetime import datetime
from backend.database import Base


class UserSentenceProgress(Base):
    __tablename__ = "user_sentence_progress"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    shared_sentence_id = Column(Integer, ForeignKey("shared_sentences.id", ondelete="CASCADE"), nullable=False, index=True)
    is_completed = Column(Boolean, default=False)
    user_attempt = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        UniqueConstraint("user_id", "shared_sentence_id", name="uq_user_sentence_progress"),
    )

    sentence = relationship("SharedSentence", back_populates="progress")
