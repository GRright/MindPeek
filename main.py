"""
perMIR - 用户画像生成系统
FastAPI主应用入口
"""
import os
import sys
from pathlib import Path
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

BASE_DIR = Path(__file__).parent
sys.path.insert(0, str(BASE_DIR))

from backend.api.routes import router as api_router
from backend.core.config import settings
from backend.knowledge_graph.graph import knowledge_graph


@asynccontextmanager
async def lifespan(app: FastAPI):
    print("正在初始化数据库...")
    data_dir = BASE_DIR / "data"
    data_dir.mkdir(exist_ok=True)
    
    db_path = data_dir / "permir.db"
    
    from backend.core.config import settings
    settings.database_url = f"sqlite+aiosqlite:///{db_path}"
    
    from backend.utils.database import setup_database
    await setup_database()
    print(f"数据库初始化完成: {db_path}")
    
    print("正在初始化知识图谱...")
    print(f"知识图谱节点数: {len(knowledge_graph.graph.nodes)}")
    print(f"知识图谱边数: {len(knowledge_graph.graph.edges)}")
    
    yield
    
    print("正在关闭服务...")


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="基于LLM的多轮对话用户画像生成系统",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix="/api")

frontend_path = Path(__file__).parent.parent / "frontend" / "dist"
if frontend_path.exists():
    app.mount("/", StaticFiles(directory=str(frontend_path), html=True), name="static")


@app.get("/")
async def root():
    return {
        "name": settings.app_name,
        "version": settings.app_version,
        "docs": "/docs",
        "api": "/api"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
