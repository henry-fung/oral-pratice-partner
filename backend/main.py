import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from backend.database import Base, engine
from backend.api import api_router

# 创建数据库表
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="口语练习助手 API",
    description="一个基于 LLM 的口语练习助手应用",
    version="1.0.0"
)

# CORS 配置
allowed_origins = os.getenv("ALLOWED_ORIGINS", "http://localhost:8000").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册 API 路由
app.include_router(api_router)

# 挂载静态文件目录（前端）
frontend_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "frontend")
if os.path.exists(frontend_dir):
    # 挂载整个 frontend 目录到根路径，这样 index.html 可以正确引用 js/ 目录
    app.mount("/", StaticFiles(directory=frontend_dir, html=True), name="static")


@app.get("/")
async def read_index():
    """返回前端首页"""
    index_path = os.path.join(frontend_dir, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return {"message": "欢迎使用口语练习助手 API！访问 /docs 查看 API 文档"}


@app.get("/api/health")
async def health_check():
    """健康检查"""
    return {"status": "healthy", "version": "1.0.0"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
