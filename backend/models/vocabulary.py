from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, DateTime, Text, UniqueConstraint
from sqlalchemy.orm import relationship
from datetime import datetime
from backend.database import Base


class Vocabulary(Base):
    __tablename__ = "vocabulary"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    word = Column(String(100), nullable=False)
    language = Column(String(20), nullable=False)
    definition = Column(Text)  # 中文释义
    example_sentence = Column(Text)  # 例句
    pronunciation = Column(Text)  # 发音
    added_from_sentence_id = Column(Integer, ForeignKey("sentences.id", ondelete="SET NULL"))
    is_mastered = Column(Boolean, default=False)  # 是否已掌握
    review_count = Column(Integer, default=0)  # 复习次数
    last_reviewed_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)

    # 关联关系
    user = relationship("User", back_populates="vocabulary")

    # 避免重复添加
    __table_args__ = (
        UniqueConstraint('user_id', 'word', 'language', name='uq_user_word_language'),
    )
