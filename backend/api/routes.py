from fastapi import APIRouter, HTTPException
from typing import Optional, List
from pydantic import BaseModel
import json
from backend.services.profile_service import ProfileService
from backend.models.schemas import ChatRequest, ChatResponse
from backend.models.database import FeatureModel
from backend.agents.async_orchestrator import get_orchestrator
from backend.knowledge_graph.graph import knowledge_graph
from backend.services.feature_merger import feature_merger
from fastapi.responses import StreamingResponse

router = APIRouter()

class ChatStreamRequest(BaseModel):
    user_id: str
    message: str
    extract_features: bool = False
    deep_think: bool = True

@router.post("/stream")
async def chat_stream(
    request: ChatStreamRequest,
) -> StreamingResponse:
    async def event_generator():
        try:
            yield f"data: {json.dumps({'type': 'start'})}\n\n"

            orchestrator = get_orchestrator()
            llm = orchestrator.llm
            if not llm:
                yield f"data: {json.dumps({'type': 'error', 'content': 'LLM 服务未初始化'})}\n\n"
                return

            system_prompt = f"""你是一个友善的AI助手，正在与用户进行对话。"""
            messages = [{"role": "system", "content": system_prompt}]

            messages.append({"role": "user", "content": request.message})

            full_response = ""
            async for chunk_text in llm.chat_stream(messages):
                full_response += chunk_text

            think_content = None
            display_content = full_response

            think_end_tag = '</think>'
            think_pos = full_response.find(think_end_tag)

            if think_pos != -1:
                think_content = full_response[:think_pos].strip()
                display_content = full_response[think_pos + len(think_end_tag):].strip()
            else:
                rich_start = full_response.find('<RichMediaReference>')
                rich_end = full_response.find('superscript:')
                if rich_start != -1 and rich_end != -1 and rich_start < rich_end:
                    think_content = full_response[rich_start + 20:rich_end].strip()
                    display_content = full_response[:rich_start] + full_response[rich_end + 11:]

            display_content = display_content.strip()

            if think_content:
                yield f"data: {json.dumps({'type': 'think', 'content': think_content})}\n\n"

            for i in range(0, len(display_content), 15):
                chunk = display_content[i:i+15]
                yield f"data: {json.dumps({'type': 'chunk', 'content': chunk})}\n\n"

            yield f"data: {json.dumps({'type': 'done', 'content': display_content, 'think_content': think_content})}\n\n"

        except Exception as e:
            import traceback
            error_msg = str(e)
            print(f"Stream error: {error_msg}")
            print(traceback.format_exc())
            yield f"data: {json.dumps({'type': 'error', 'content': f'错误: {error_msg}'})}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")


@router.post("/chat", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
):
    orchestrator = get_orchestrator()

    messages = [{"role": "system", "content": "你是一个友善的AI助手，正在与用户进行对话。"}]
    messages.append({"role": "user", "content": request.message})

    full_response = ""
    async for chunk_text in orchestrator.llm.chat_stream(messages):
        full_response += chunk_text

    think_content = None
    display_content = full_response

    think_end_tag = '</think>'
    think_pos = full_response.find(think_end_tag)

    if think_pos != -1:
        think_content = full_response[:think_pos].strip()
        display_content = full_response[think_pos + len(think_end_tag):].strip()
    else:
        rich_start = full_response.find('<RichMediaReference>')
        rich_end = full_response.find('superscript:')
        if rich_start != -1 and rich_end != -1 and rich_start < rich_end:
            think_content = full_response[rich_start + 20:rich_end].strip()
            display_content = full_response[:rich_start] + full_response[rich_end + 11:]

    return ChatResponse(response=display_content.strip(), think_content=think_content)

@router.get("/profile/{user_id}/conversations")
async def get_conversations(
    user_id: str,
    limit: int = 20,
):
    from backend.utils.database import DatabaseSession
    async with DatabaseSession() as session:
        service = ProfileService(session)
        conversations = await service.get_conversation_history(user_id, limit=limit)
        return conversations

@router.delete("/profile/{user_id}/conversations")
async def delete_conversation(
    user_id: str,
):
    from backend.utils.database import DatabaseSession
    async with DatabaseSession() as session:
        service = ProfileService(session)
        await service.clear_conversation_history(user_id)
        return {"status": "success", "message": "对话历史已清除"}

@router.get("/profile/{user_id}")
async def get_profile(
    user_id: str,
):
    from backend.utils.database import DatabaseSession
    async with DatabaseSession() as session:
        service = ProfileService(session)
        try:
            profile = await service.get_user_profile_detail(user_id)
            if not profile:
                raise HTTPException(status_code=404, detail="用户画像不存在")
            return profile
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

@router.get("/health")
async def health_check():
    return {"status": "healthy"}

@router.post("/features/{user_id}/merge-duplicates")
async def merge_duplicate_features(user_id: str, threshold: float = 0.75):
    """智能合并用户的重复特征"""
    from backend.utils.database import DatabaseSession
    async with DatabaseSession() as session:
        service = ProfileService(session)
        try:
            user_features, _ = await service.get_user_features(user_id)
            
            feature_dicts = []
            for f in user_features:
                feature_dicts.append({
                    "id": f.id,
                    "feature_type": f.feature_type,
                    "feature_value": f.feature_value,
                    "confidence": f.confidence,
                    "notes": f.notes
                })
            
            duplicates = feature_merger.detect_duplicates(feature_dicts, threshold)
            
            merged_count = 0
            for feat1, feat2, similarity in duplicates:
                existing_feature = None
                for f in user_features:
                    if f.id == feat1["id"]:
                        existing_feature = f
                        break
                
                if existing_feature:
                    existing_confidence = existing_feature.confidence
                    new_confidence = (existing_confidence + feat2.get("confidence", 0.5)) / 2
                    
                    existing_notes = existing_feature.notes or ""
                    if existing_notes:
                        existing_notes += f"\n合并: {feat2['feature_value']} (相似度: {similarity:.2f})"
                    else:
                        existing_notes = f"合并: {feat2['feature_value']} (相似度: {similarity:.2f})"
                    
                    existing_feature.confidence = new_confidence
                    existing_feature.notes = existing_notes
                    
                    from sqlalchemy import select
                    feat2_to_delete = await session.execute(
                        select(FeatureModel).where(FeatureModel.id == feat2["id"])
                    )
                    feat2_obj = feat2_to_delete.scalar_one_or_none()
                    if feat2_obj:
                        feat2_obj.is_active = False
                    
                    merged_count += 1
            
            await session.commit()
            
            return {
                "status": "success",
                "duplicates_found": len(duplicates),
                "merged_count": merged_count
            }
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

@router.get("/knowledge-graph/{user_id}")
async def get_knowledge_graph(user_id: str):
    from backend.utils.database import DatabaseSession
    async with DatabaseSession() as session:
        service = ProfileService(session)
        try:
            user_features, _ = await service.get_user_features(user_id)
            feature_dicts = []
            for feature in user_features:
                feature_dicts.append({
                    "feature_type": feature.feature_type,
                    "feature_value": feature.feature_value
                })
            
            graph_data = knowledge_graph.get_user_subgraph(feature_dicts)
            
            nodes = []
            edges = []
            for node in graph_data.get("nodes", []):
                nodes.append({
                    "id": node["id"],
                    "label": node["node_name"],
                    "type": node["node_type"]
                })
            
            for edge in graph_data.get("edges", []):
                edges.append({
                    "source": edge["source_id"],
                    "target": edge["target_id"],
                    "relation": edge["relation_type"],
                    "inferred": edge.get("weight", 1.0) < 1.0
                })
            
            return {"nodes": nodes, "edges": edges}
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
