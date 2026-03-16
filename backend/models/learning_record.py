from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Float
from sqlalchemy.orm import relationship
from datetime import datetime
from backend.database import Base


class LearningRecord(Base):
    __tablename__ = "learning_records"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    sentence_id = Column(Integer, ForeignKey("sentences.id", ondelete="SET NULL"), nullable=True)
    scenario_id = Column(Integer, ForeignKey("scenarios.id", ondelete="SET NULL"), nullable=True)
    action_type = Column(String(50), nullable=False)  # sentence_practiced, scenario_completed, word_added
    time_spent_seconds = Column(Integer)  # 花费时间
    accuracy_score = Column(Float)  # 准确度（如有评分）
    created_at = Column(DateTime, default=datetime.utcnow, index=True)

    # 关联关系
    user = relationship("User", back_populates="learning_records")
