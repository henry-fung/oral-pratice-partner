from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, DateTime, Text
from sqlalchemy.orm import relationship
from datetime import datetime
from backend.database import Base


class Scenario(Base):
    __tablename__ = "scenarios"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    session_id = Column(String(50), nullable=False, index=True)  # 关联一次生成的 N 个场景
    title = Column(String(200), nullable=False)  # 场景标题
    description = Column(Text)  # 场景描述
    context = Column(Text)  # 场景上下文
    role = Column(String(50), nullable=False)  # 关联的用户角色
    language = Column(String(20), nullable=False)  # 目标语言
    is_selected = Column(Boolean, default=False)  # 用户是否选择了该场景
    created_at = Column(DateTime, default=datetime.utcnow, index=True)

    # 关联关系
    user = relationship("User", back_populates="scenarios")
    sentences = relationship("Sentence", back_populates="scenario", cascade="all, delete-orphan")
