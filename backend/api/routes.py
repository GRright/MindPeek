"""
FastAPI路由定义
"""
import json
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from ..utils.database import get_async_session
from ..models.schemas import (
    ChatRequest, ChatResponse, FeatureCreate, FeatureResponse,
    MessageCreate, MessageResponse, ProfileResponse, ProfileSummary,
    LLMConfigRequest, LLMConfigResponse, UserProfileDetail,
    KnowledgeGraphResponse, AgentTaskRequest, AgentTaskResponse
)
from ..services.profile_service import ProfileService
from ..services.llm_provider import LLMProviderFactory
from ..knowledge_graph.graph import knowledge_graph
from ..core.config import config_manager


router = APIRouter()


async def get_profile_service(db: AsyncSession = Depends(get_async_session)) -> ProfileService:
    return ProfileService(db)


@router.post("/chat", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    service: ProfileService = Depends(get_profile_service)
):
    """发送聊天消息并提取特征"""
    try:
        result = await service.process_chat(
            user_id=request.user_id,
            message=request.message,
            extract_features=request.extract_features
        )
        
        return ChatResponse(
            response="消息已处理",
            features_extracted=result["extracted_features"],
            profile_updated=True,
            session_id=request.session_id
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/profile/{user_id}", response_model=UserProfileDetail)
async def get_profile(
    user_id: str,
    service: ProfileService = Depends(get_profile_service)
):
    """获取用户画像详情"""
    try:
        return await service.get_user_profile_detail(user_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/profile/{user_id}/summary", response_model=ProfileSummary)
async def get_profile_summary(
    user_id: str,
    service: ProfileService = Depends(get_profile_service)
):
    """获取用户画像摘要"""
    try:
        detail = await service.get_user_profile_detail(user_id)
        return detail.summary
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/profile/{user_id}/features", response_model=List[FeatureResponse])
async def get_features(
    user_id: str,
    feature_type: Optional[str] = Query(None),
    service: ProfileService = Depends(get_profile_service)
):
    """获取用户特征列表"""
    try:
        features = await service.get_user_features(user_id, feature_type)
        return [FeatureResponse.from_orm(f) for f in features]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/profile/{user_id}/features", response_model=FeatureResponse)
async def add_feature(
    user_id: str,
    feature: FeatureCreate,
    service: ProfileService = Depends(get_profile_service)
):
    """手动添加特征"""
    try:
        result = await service.add_feature(user_id, feature)
        return FeatureResponse.from_orm(result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/profile/{user_id}/conversations", response_model=List[MessageResponse])
async def get_conversations(
    user_id: str,
    limit: int = Query(50, ge=1, le=200),
    service: ProfileService = Depends(get_profile_service)
):
    """获取对话历史"""
    try:
        conversations = await service.get_conversation_history(user_id, limit)
        return [MessageResponse.from_orm(c) for c in conversations]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/knowledge-graph", response_model=KnowledgeGraphResponse)
async def get_knowledge_graph():
    """获取完整知识图谱"""
    try:
        graph_data = knowledge_graph.export_graph()
        return KnowledgeGraphResponse(**graph_data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/knowledge-graph/{user_id}", response_model=KnowledgeGraphResponse)
async def get_user_knowledge_graph(user_id: str):
    """获取用户相关知识图谱"""
    try:
        graph_data = knowledge_graph.get_user_subgraph(user_id)
        return KnowledgeGraphResponse(**graph_data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/llm/providers", response_model=List[LLMConfigResponse])
async def get_llm_providers():
    """获取可用的LLM提供者列表"""
    providers = LLMProviderFactory.get_available_providers()
    result = []
    
    for provider in providers:
        config = config_manager.get_llm_config(provider)
        result.append(LLMConfigResponse(
            provider=provider,
            enabled=config.enabled,
            model=config.model,
            configured=bool(config.api_key) or provider == "ollama"
        ))
    
    return result


@router.post("/llm/config")
async def update_llm_config(request: LLMConfigRequest):
    """更新LLM配置"""
    try:
        config_manager.update_llm_config(
            provider=request.provider,
            api_key=request.api_key,
            model=request.model,
            api_url=request.api_url
        )
        LLMProviderFactory.clear_instances()
        return {"message": "配置更新成功"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health")
async def health_check():
    """健康检查"""
    return {"status": "healthy", "service": "perMIR"}
