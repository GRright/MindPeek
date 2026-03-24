"""
数据库连接工具
"""
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

from ..core.config import settings


engine = None
async_session_maker = None


async def setup_database():
    global engine, async_session_maker
    
    engine = create_async_engine(settings.database_url, echo=False)
    async_session_maker = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with engine.begin() as conn:
        from ..models.database import Base
        await conn.run_sync(Base.metadata.create_all)
        
        await _apply_migrations(conn)
    
    return engine, async_session_maker


async def _apply_migrations(conn):
    """应用数据库迁移"""
    try:
        from sqlalchemy import text
        
        result = await conn.execute(text("PRAGMA table_info(features)"))
        columns = [row[1] for row in result.fetchall()]
        
        if 'notes' not in columns:
            print("正在添加 notes 列到 features 表...")
            await conn.execute(text("ALTER TABLE features ADD COLUMN notes TEXT"))
            print("notes 列添加成功")
        
        if 'verification_count' not in columns:
            print("正在添加 verification_count 列到 features 表...")
            await conn.execute(text("ALTER TABLE features ADD COLUMN verification_count INTEGER DEFAULT 0"))
            print("verification_count 列添加成功")
        
        if 'last_verified_at' not in columns:
            print("正在添加 last_verified_at 列到 features 表...")
            await conn.execute(text("ALTER TABLE features ADD COLUMN last_verified_at DATETIME"))
            print("last_verified_at 列添加成功")
    
    except Exception as e:
        print(f"迁移警告: {e}")


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """用于 FastAPI Depends 的依赖"""
    session = async_session_maker()
    try:
        yield session
        await session.commit()
    except Exception:
        await session.rollback()
        raise
    finally:
        await session.close()


class DatabaseSession:
    """用于手动数据库会话管理的上下文管理器"""
    def __init__(self):
        self.session = None

    async def __aenter__(self) -> AsyncSession:
        self.session = async_session_maker()
        return self.session

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            if exc_type:
                await self.session.rollback()
            else:
                await self.session.commit()
            await self.session.close()
        return False
