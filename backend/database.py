import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    DATABASE_URL = "sqlite:///./oral_practice.db"

# PostgreSQL 需要特殊处理连接池
if DATABASE_URL.startswith("postgresql"):
    engine = create_engine(
        DATABASE_URL.replace("postgres://", "postgresql://"),
        pool_size=20,
        max_overflow=40,
        pool_pre_ping=True,
        echo=False
    )
else:
    engine = create_engine(
        DATABASE_URL,
        connect_args={"check_same_thread": False},
        echo=False
    )

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    """依赖注入：获取数据库会话"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
