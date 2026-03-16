from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime
from backend.database import Base


class UserProfile(Base):
    __tablename__ = "user_profiles"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)
    role = Column(String(50), nullable=False)  # 留学生、商务人士、旅游者等
    custom_role_name = Column(String(100), nullable=True)  # 自定义角色名称
    target_language = Column(String(20), nullable=False)  # en, ja, fr, es 等
    native_language = Column(String(20), default="zh")  # 默认中文
    proficiency_level = Column(String(20), default="intermediate")  # beginner, intermediate, advanced
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 关联关系
    user = relationship("User", back_populates="profile")
