"""
perMIR - 用户画像生成系统
FastAPI主应用入口
"""
import os
import sys
from pathlib import Path
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

BASE_DIR = Path(__file__).parent
sys.path.insert(0, str(BASE_DIR))

from backend.api.routes import router as api_router
from backend.core.config import settings
from backend.knowledge_graph.graph import knowledge_graph


@asynccontextmanager
async def lifespan(app: FastAPI):
    print("正在初始化数据库...")
    
    from backend.core.config import config_manager
    
    db_path = config_manager.get_database_path()
    db_dir = Path(db_path).parent
    db_dir.mkdir(parents=True, exist_ok=True)
    
    from backend.core.config import settings
    settings.database_url = f"sqlite+aiosqlite:///{db_path}"

    from backend.utils.database import setup_database
    await setup_database()
    print(f"数据库初始化完成: {db_path}")

    print("正在初始化知识图谱...")
    from backend.knowledge_graph.graph import PersonalityKnowledgeBase
    kb = PersonalityKnowledgeBase()
    print(f"知识图谱预定义类别数: {len(kb.FEATURE_CATEGORIES)}")

    yield

    print("正在关闭服务...")


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="基于LLM的多轮对话用户画像生成系统",
    lifespan=lifespan,
    docs_url=settings.debug and "/docs" or None,
    redoc_url=settings.debug and "/redoc" or None
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization"],
)

from fastapi.middleware.trustedhost import TrustedHostMiddleware
from backend.core.security import RateLimitMiddleware

app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=["localhost", "127.0.0.1", "*"]
)

app.add_middleware(RateLimitMiddleware)

from fastapi.responses import Response

@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Content-Security-Policy"] = "default-src 'self'; script-src 'self' 'unsafe-inline' 'unsafe-eval'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; font-src 'self';"
    return response

app.include_router(api_router, prefix="/api")


# 静态文件路由（在 API 路由之后）
frontend_dist = BASE_DIR / "frontend" / "dist"
if frontend_dist.exists():
    app.mount("/assets", StaticFiles(directory=str(frontend_dist / "assets")), name="assets")


@app.get("/")
async def root():
    index_path = frontend_dist / "index.html"
    if index_path.exists():
        return FileResponse(str(index_path))
    return JSONResponse({
        "name": settings.app_name,
        "version": settings.app_version,
        "docs": "/docs",
        "api": "/api"
    })


# SPA 通配符路由（必须在最后）
@app.get("/{path:path}")
async def serve_spa(path: str):
    # 排除 API 和文档路径
    if path.startswith("api") or path in ["docs", "redoc", "openapi.json"]:
        return JSONResponse({"error": "Not found"}, status_code=404)

    if "." in path:
        file_path = frontend_dist / path
        if file_path.exists():
            return FileResponse(str(file_path))

    index_path = frontend_dist / "index.html"
    if index_path.exists():
        return FileResponse(str(index_path))
    return JSONResponse({
        "name": settings.app_name,
        "version": settings.app_version,
        "docs": "/docs",
        "api": "/api"
    })


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
