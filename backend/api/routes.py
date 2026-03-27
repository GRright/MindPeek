from fastapi import APIRouter, HTTPException
from typing import Optional, List
from pydantic import BaseModel
import json
import asyncio
from backend.services.profile_service import ProfileService
from backend.models.schemas import ChatRequest, ChatResponse
from backend.models.database import FeatureModel
from backend.agents.async_orchestrator import get_orchestrator, TaskType
from backend.knowledge_graph.graph import knowledge_graph
from backend.services.feature_merger import feature_merger
from fastapi.responses import StreamingResponse
from backend.utils.sync_database import save_conversation_sync, save_feature_sync
from backend.utils.sync_feature_extractor import extract_features_sync

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

            system_prompt = f"""你是一个友善的 AI 助手，正在与用户进行对话。"""
            messages = [{"role": "system", "content": system_prompt}]

            messages.append({"role": "user", "content": request.message})

            full_response = ""
            llm_error = None
            
            try:
                async for chunk_text in llm.chat_stream(messages):
                    full_response += chunk_text
                    yield f"data: {json.dumps({'type': 'chunk', 'content': chunk_text})}\n\n"
            except Exception as e:
                llm_error = str(e)
                full_response = ""
                yield f"data: {json.dumps({'type': 'error', 'content': f'AI 服务暂时不可用：{llm_error}'})}\n\n"

            display_content = full_response
            think_content = None  # 初始化 think_content

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

            # 如果有 think 内容，在流式结束后发送
            if think_content:
                yield f"data: {json.dumps({'type': 'think', 'content': think_content})}\n\n"

            # 发送完成信号
            yield f"data: {json.dumps({'type': 'done', 'content': display_content, 'think_content': think_content})}\n\n"

            # 使用同步方式保存对话（避免异步连接池问题）
            print(f"\n>>> 开始使用同步方式保存对话 for user_id: {request.user_id}")
            
            # 保存用户消息
            save_conversation_sync(request.user_id, "user", request.message, "default")
            
            # 保存助手回复
            save_conversation_sync(request.user_id, "assistant", display_content if display_content else "(无回复内容)", "default")
            
            print(f">>> 同步保存对话完成\n")
            
            # 如果需要提取特征 - 在后台执行，不阻塞流式响应
            if request.extract_features:
                print(f">>> 开始特征提取 for user_id: {request.user_id}")
                try:
                    # 使用 asyncio 创建后台任务执行特征提取
                    import asyncio
                    asyncio.create_task(
                        async_extract_features(request.user_id, request.message, display_content if display_content else "(无回复内容)")
                    )
                    print(f">>> 特征提取任务已创建\n")
                except Exception as fe_error:
                    print(f">>> 特征提取任务创建失败：{fe_error}")
                    import traceback
                    print(traceback.format_exc())

        except Exception as e:
            import traceback
            error_msg = str(e)
            print(f"Stream error: {error_msg}")
            print(traceback.format_exc())
            yield f"data: {json.dumps({'type': 'error', 'content': f'错误：{error_msg}'})}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")


async def async_extract_features(user_id: str, message: str, response: str):
    """异步执行特征提取，不阻塞流式响应"""
    try:
        # 在后台线程中执行同步的特征提取
        import asyncio
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(
            None, 
            extract_features_sync, 
            user_id, 
            message, 
            response
        )
        print(f">>> 后台特征提取完成")
    except Exception as e:
        print(f">>> 后台特征提取失败: {e}")
        import traceback
        print(traceback.format_exc())


@router.post("/chat", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
):
    orchestrator = get_orchestrator()

    messages = [{"role": "system", "content": "你是一个友善的 AI 助手，正在与用户进行对话。"}]
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
    """使用同步方式获取用户画像"""
    from backend.utils.sync_database import get_user_features_sync
    import sqlite3
    
    try:
        # 同步获取特征
        features = get_user_features_sync(user_id)
        
        # 同步获取对话统计
        conn = sqlite3.connect('C:\\myProject\\MindPeek\\data\\permir.db')
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT COUNT(*) FROM conversations WHERE user_id = ?
        """, (user_id,))
        conversation_count = cursor.fetchone()[0]
        
        cursor.execute("""
            SELECT MIN(timestamp), MAX(timestamp) FROM conversations WHERE user_id = ?
        """, (user_id,))
        time_range = cursor.fetchone()
        
        conn.close()
        
        # 按类型分组特征
        features_by_type = {}
        for f in features:
            ftype = f.get('feature_type', '未知')
            if ftype not in features_by_type:
                features_by_type[ftype] = []
            features_by_type[ftype].append(f)
        
        # 从特征中计算大五人格分数
        big_five = calculate_big_five(features)
        
        # 尝试从特征中提取 MBTI
        mbti = extract_mbti_from_features(features)
        
        return {
            "user_id": user_id,
            "features": features,
            "summary": {
                "conversation_count": conversation_count,
                "feature_count": len(features),
                "first_conversation": str(time_range[0]) if time_range[0] else None,
                "last_conversation": str(time_range[1]) if time_range[1] else None,
                "big_five": big_five,
                "mbti": mbti
            },
            "features_by_type": features_by_type
        }
    except Exception as e:
        import traceback
        print(f"获取用户画像失败：{e}")
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))

def calculate_big_five(features):
    """根据特征计算大五人格分数"""
    big_five = {
        "开放性": 50,
        "尽责性": 50,
        "外向性": 50,
        "宜人性": 50,
        "神经质": 50
    }

    openness_keywords = ["看书", "学习", "思考", "创新", "好奇", "艺术"]
    conscientiousness_keywords = ["规律", "计划", "自律", "坚持", "负责", "加班"]
    extraversion_keywords = ["社交", "朋友", "聚会", "健谈", "活泼", "开朗"]
    agreeableness_keywords = ["友善", "随和", "体贴", "合作", "信任"]
    neuroticism_keywords = ["焦虑", "担忧", "敏感", "情绪化", "孤独", "压力"]

    openness_count = 0
    conscientiousness_count = 0
    extraversion_count = 0
    agreeableness_count = 0
    neuroticism_count = 0

    for f in features:
        fvalue = f.get('feature_value', '').lower()
        ftype = f.get('feature_type', '')
        confidence = f.get('confidence', 0.5)

        if any(kw in fvalue for kw in openness_keywords):
            openness_count += confidence
        elif '内向' in fvalue or '独处' in fvalue or '宅' in fvalue:
            openness_count += confidence * 0.3

        if any(kw in fvalue for kw in conscientiousness_keywords):
            conscientiousness_count += confidence
        elif '拖延' in fvalue or '懒' in fvalue:
            conscientiousness_count -= confidence * 0.5

        if any(kw in fvalue for kw in extraversion_keywords):
            extraversion_count += confidence
        elif '宅' in fvalue or '内向' in fvalue or '朋友较少' in fvalue:
            extraversion_count -= confidence * 0.5

        if any(kw in fvalue for kw in agreeableness_keywords):
            agreeableness_count += confidence

        if any(kw in fvalue for kw in neuroticism_keywords):
            neuroticism_count += confidence
        elif '随缘' in fvalue or '平淡' in fvalue:
            neuroticism_count -= confidence * 0.3

    big_five["开放性"] = max(0, min(100, 50 + (openness_count - 1) * 10))
    big_five["尽责性"] = max(0, min(100, 50 + (conscientiousness_count - 1) * 10))
    big_five["外向性"] = max(0, min(100, 50 + (extraversion_count - 1) * 10))
    big_five["宜人性"] = max(0, min(100, 50 + (agreeableness_count - 1) * 10))
    big_five["神经质"] = max(0, min(100, 50 + (neuroticism_count - 1) * 10))

    return big_five

def extract_mbti_from_features(features):
    """从特征中提取 MBTI"""
    for f in features:
        if f.get('feature_type') == 'MBTI' or f.get('feature_type') == '个人信息':
            value = f.get('feature_value', '')
            if 'INT' in value or 'INF' in value or 'IST' in value or 'ISF' in value:
                return value
    return None

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
                        existing_notes += f"\n合并：{feat2['feature_value']} (相似度：{similarity:.2f})"
                    else:
                        existing_notes = f"合并：{feat2['feature_value']} (相似度：{similarity:.2f})"
                    
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
                    "inferred": edge.get("weight", 1.0) < 1.0,
                    "weight": edge.get("weight", 1.0)
                })
            
            feature_types = list(set([
                feature.feature_type for feature in user_features
            ]))
            return {"nodes": nodes, "edges": edges, "featureTypes": feature_types}
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
