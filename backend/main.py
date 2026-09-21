import os
import asyncio
from datetime import datetime
from zoneinfo import ZoneInfo
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from backend.database import Base, engine
import backend.models  # noqa: F401 — ensures all models are registered before create_all
from backend.api import api_router

# 创建数据库表
Base.metadata.create_all(bind=engine)

# 迁移：为已有数据库添加 is_practiced 列
from sqlalchemy import text
with engine.connect() as _conn:
    try:
        _conn.execute(text("ALTER TABLE user_scenarios ADD COLUMN is_practiced BOOLEAN NOT NULL DEFAULT 0"))
        _conn.commit()
    except Exception:
        pass
    try:
        _conn.execute(text("ALTER TABLE user_scenarios ADD COLUMN last_active_sentence_id INTEGER REFERENCES shared_sentences(id)"))
        _conn.commit()
    except Exception:
        pass
    try:
        _conn.execute(text("ALTER TABLE vocabulary ADD COLUMN audio_url TEXT"))
        _conn.commit()
    except Exception:
        pass
    try:
        _conn.execute(text("ALTER TABLE shared_sentences ADD COLUMN parent_sentence_id INTEGER REFERENCES shared_sentences(id)"))
        _conn.commit()
    except Exception:
        pass
    try:
        _conn.execute(text("ALTER TABLE shared_sentences ADD COLUMN context_text TEXT"))
        _conn.commit()
    except Exception:
        pass
    try:
        _conn.execute(text("ALTER TABLE shared_sentences ADD COLUMN context_native TEXT"))
        _conn.commit()
    except Exception:
        pass
    try:
        _conn.execute(text("ALTER TABLE shared_scenarios ADD COLUMN visibility VARCHAR(20) NOT NULL DEFAULT 'shared'"))
        _conn.commit()
    except Exception:
        pass
    try:
        _conn.execute(text("ALTER TABLE shared_scenarios ADD COLUMN owner_user_id INTEGER REFERENCES users(id)"))
        _conn.commit()
    except Exception:
        pass
    try:
        _conn.execute(text("ALTER TABLE shared_scenarios ADD COLUMN is_custom BOOLEAN NOT NULL DEFAULT 0"))
        _conn.commit()
    except Exception:
        pass
    try:
        _conn.execute(text("ALTER TABLE shared_scenarios ADD COLUMN news_topic_id INTEGER REFERENCES news_topics(id)"))
        _conn.commit()
    except Exception:
        pass
    for statement in (
        "ALTER TABLE user_profiles ADD COLUMN news_interests TEXT NOT NULL DEFAULT '[]'",
        "ALTER TABLE news_topics ADD COLUMN content_language VARCHAR(20)",
        "ALTER TABLE news_topics ADD COLUMN source_type VARCHAR(30) NOT NULL DEFAULT 'news'",
        "ALTER TABLE news_topics ADD COLUMN content_category VARCHAR(50)",
        "ALTER TABLE news_topics ADD COLUMN extracted_text TEXT",
        "ALTER TABLE news_topics ADD COLUMN evidence_json TEXT NOT NULL DEFAULT '{}'",
        "ALTER TABLE news_topics ADD COLUMN extraction_status VARCHAR(30) NOT NULL DEFAULT 'summary_only'",
    ):
        try:
            _conn.execute(text(statement))
            _conn.commit()
        except Exception:
            pass

app = FastAPI(
    title="口语练习助手 API",
    description="一个基于 LLM 的口语练习助手应用",
    version="1.0.0"
)

_news_scheduler_task = None


async def _daily_news_scheduler():
    """Best-effort in-process scheduler; refresh requests remain the catch-up path."""
    from backend.database import SessionLocal
    from backend.models.profile import UserProfile
    from backend.api.scenarios import _get_daily_news_topics
    last_run = None
    hour = int(os.getenv("NEWS_REFRESH_HOUR", "7"))
    while True:
        now = datetime.now(ZoneInfo("Asia/Shanghai"))
        if now.hour >= hour and last_run != now.date():
            db = SessionLocal()
            try:
                profiles = db.query(UserProfile).all()
                seen = set()
                for profile in profiles:
                    key = (profile.role, profile.target_language, profile.news_interests or "")
                    if key not in seen:
                        seen.add(key)
                        await _get_daily_news_topics(db, profile)
                last_run = now.date()
            finally:
                db.close()
        await asyncio.sleep(60)


@app.on_event("startup")
async def start_news_scheduler():
    global _news_scheduler_task
    _news_scheduler_task = asyncio.create_task(_daily_news_scheduler())


@app.on_event("shutdown")
async def stop_news_scheduler():
    if _news_scheduler_task:
        _news_scheduler_task.cancel()

# CORS 配置
allowed_origins = os.getenv("ALLOWED_ORIGINS", "http://localhost:8000").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册 API 路由（必须在静态文件之前）
app.include_router(api_router)

# 健康检查（必须在静态文件之前定义）
@app.get("/api/health")
async def health_check():
    """健康检查"""
    return {"status": "healthy", "version": "1.0.0"}

# 静态文件服务（必须在 API 路由之后，避免拦截 API 请求）
frontend_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "frontend")
if os.path.exists(frontend_dir):
    app.mount("/", StaticFiles(directory=frontend_dir, html=True), name="static")

@app.get("/")
async def read_index():
    """返回前端首页"""
    index_path = os.path.join(frontend_dir, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return {"message": "欢迎使用口语练习助手 API！访问 /docs 查看 API 文档"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
