from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, DateTime, Text
from sqlalchemy.orm import relationship
from datetime import datetime
from backend.database import Base


class Sentence(Base):
    __tablename__ = "sentences"

    id = Column(Integer, primary_key=True, index=True)
    scenario_id = Column(Integer, ForeignKey("scenarios.id", ondelete="CASCADE"), nullable=False, index=True)
    native_text = Column(Text, nullable=False)  # 中文句子
    target_text = Column(Text, nullable=False)  # 目标语言句子
    pronunciation_guide = Column(Text)  # 发音指导（如 IPA 或拼音）
    difficulty_level = Column(String(20), default="intermediate")
    sentence_order = Column(Integer, default=1)  # 场景中的句子顺序
    is_completed = Column(Boolean, default=False)  # 用户是否完成练习
    user_attempt = Column(Text)  # 用户的尝试（可选录音或文字）
    created_at = Column(DateTime, default=datetime.utcnow)

    # 关联关系
    scenario = relationship("Scenario", back_populates="sentences")
