"""
数据库模型定义
"""
from datetime import datetime
from typing import Optional, List
from sqlalchemy import Column, Integer, String, Float, Text, DateTime, JSON, ForeignKey, Boolean
from sqlalchemy.orm import DeclarativeBase, relationship
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker


class Base(DeclarativeBase):
    pass


class UserModel(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String(100), unique=True, nullable=False, index=True)
    username = Column(String(100), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    profile = relationship("ProfileModel", back_populates="user", uselist=False)
    conversations = relationship("ConversationModel", back_populates="user")
    features = relationship("FeatureModel", back_populates="user")
    relationships = relationship("RelationshipModel", back_populates="user")


class ProfileModel(Base):
    __tablename__ = "profiles"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String(100), ForeignKey("users.user_id"), unique=True, nullable=False)
    profile_data = Column(JSON, default=dict)
    summary = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    user = relationship("UserModel", back_populates="profile")


class ConversationModel(Base):
    __tablename__ = "conversations"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String(100), ForeignKey("users.user_id"), nullable=False, index=True)
    role = Column(String(20), nullable=False)
    content = Column(Text, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    session_id = Column(String(100), nullable=True, index=True)
    
    user = relationship("UserModel", back_populates="conversations")


class FeatureModel(Base):
    __tablename__ = "features"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String(100), ForeignKey("users.user_id"), nullable=False, index=True)
    feature_type = Column(String(50), nullable=False, index=True)
    feature_value = Column(String(500), nullable=False)
    confidence = Column(Float, default=0.0)
    source_message = Column(Text, nullable=True)
    reasoning = Column(Text, nullable=True)
    evidence = Column(JSON, default=list)
    notes = Column(Text, nullable=True)
    verification_count = Column(Integer, default=0)
    last_verified_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_confirmed_at = Column(DateTime, default=datetime.utcnow)
    is_active = Column(Boolean, default=True)
    decay_enabled = Column(Boolean, default=True)
    stability_period_days = Column(Integer, default=30)
    decay_rate = Column(Float, default=0.05)
    last_stability_eval_at = Column(DateTime, nullable=True)

    user = relationship("UserModel", back_populates="features")


class RelationshipModel(Base):
    __tablename__ = "relationships"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String(100), ForeignKey("users.user_id"), nullable=False, index=True)
    person_name = Column(String(200), nullable=False)
    relationship_type = Column(String(50), nullable=False)
    interaction_pattern = Column(Text, nullable=True)
    evidence = Column(JSON, default=list)
    confidence = Column(Float, default=0.0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_confirmed_at = Column(DateTime, default=datetime.utcnow)
    is_active = Column(Boolean, default=True)
    decay_enabled = Column(Boolean, default=True)

    user = relationship("UserModel", back_populates="relationships")


class KnowledgeNodeModel(Base):
    __tablename__ = "knowledge_nodes"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    node_type = Column(String(50), nullable=False, index=True)
    node_name = Column(String(200), nullable=False)
    properties = Column(JSON, default=dict)
    created_at = Column(DateTime, default=datetime.utcnow)


class KnowledgeEdgeModel(Base):
    __tablename__ = "knowledge_edges"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    source_id = Column(Integer, ForeignKey("knowledge_nodes.id"), nullable=False)
    target_id = Column(Integer, ForeignKey("knowledge_nodes.id"), nullable=False)
    relation_type = Column(String(100), nullable=False)
    weight = Column(Float, default=1.0)
    properties = Column(JSON, default=dict)
    created_at = Column(DateTime, default=datetime.utcnow)


class AgentTaskModel(Base):
    __tablename__ = "agent_tasks"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    task_type = Column(String(50), nullable=False)
    status = Column(String(20), default="pending")
    input_data = Column(JSON, default=dict)
    output_data = Column(JSON, default=dict)
    agent_name = Column(String(100), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)


async def init_db(database_url: str):
    engine = create_async_engine(database_url, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    return engine, async_session
