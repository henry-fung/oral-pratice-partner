from sqlalchemy import Column, Integer, String, Boolean, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime
from backend.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(100), unique=True, index=True)
    password_hash = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 关联关系
    profile = relationship("UserProfile", back_populates="user", uselist=False, cascade="all, delete-orphan")
    scenarios = relationship("Scenario", back_populates="user", cascade="all, delete-orphan")
    vocabulary = relationship("Vocabulary", back_populates="user", cascade="all, delete-orphan")
    learning_records = relationship("LearningRecord", back_populates="user", cascade="all, delete-orphan")
