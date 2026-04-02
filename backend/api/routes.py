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
from backend.utils.sync_database import (
    save_conversation_sync, 
    save_feature_sync,
    get_user_predictions_sync,
    get_cached_predictions_sync,
    save_predictions_sync,
    get_user_conversations_sync,
    get_user_features_sync
)
from backend.utils.sync_feature_extractor import extract_features_sync

router = APIRouter()

class ChatStreamRequest(BaseModel):
    user_id: str
    message: str
    extract_features: bool = False
    deep_think: bool = True


def _should_use_personalization(message: str) -> bool:
    """判断是否使用个性化 - 基于规则"""
    message_lower = message.lower()
    
    general_keywords = [
        "什么是", "如何", "怎么", "为什么", "介绍一下",
        "请问", "告诉我", "解释一下", "计算", "定义",
        "搜索", "查找", "翻译", "天气", "时间",
        "写作文", "写文章", "帮我写", "代码", "程序",
        "公式", "定理", "历史", "地理", "科学",
        "百科", "知识", "概念", "定义是", "原理"
    ]
    
    personal_keywords = [
        "我喜欢", "我的", "我觉得", "我想", "我最近",
        "我的性格", "我是", "我的爱好", "我的习惯",
        "你觉得我", "我是怎么样的人", "我的特点",
        "推荐", "建议我", "适合我", "帮我选",
        "我该怎么办", "我该怎么做", "给我推荐",
        "我应该", "对我", "根据我的", "选择"
    ]
    
    emotional_keywords = [
        "难过", "开心", "焦虑", "压力", "烦恼",
        "困扰", "迷茫", "孤独", "无聊", "累",
        "心情", "情绪", "郁闷", "沮丧", "紧张"
    ]
    
    for keyword in emotional_keywords:
        if keyword in message_lower:
            return True
    
    for keyword in personal_keywords:
        if keyword in message_lower:
            return True
    
    for keyword in general_keywords:
        if keyword in message_lower:
            return False
    
    return True


def _build_personalization_prompt(features: list, message: str) -> str:
    """构建个性化提示词"""
    if not features:
        return """你是一个友善的AI助手，正在与用户进行对话。

## 回复要求
1. 直接回答用户的问题
2. 保持回复简洁、自然
3. 像朋友间的对话一样亲切

请直接回答。"""
    
    context_parts = ["\n## 用户画像信息"]
    
    personal_info = {}
    for f in features:
        if f.get("feature_type") == "个人信息" and f.get("confidence", 0) >= 0.7:
            value = f.get("feature_value", "")
            if "姓名" in value:
                personal_info["name"] = value.replace("姓名：", "").strip()
            elif "职业" in value:
                personal_info["occupation"] = value.replace("职业：", "").strip()
            elif "居住地" in value:
                personal_info["location"] = value.replace("居住地：", "").strip()
    
    if personal_info:
        info_strs = []
        if personal_info.get("name"):
            info_strs.append(f"姓名: {personal_info['name']}")
        if personal_info.get("occupation"):
            info_strs.append(f"职业: {personal_info['occupation']}")
        if personal_info.get("location"):
            info_strs.append(f"居住地: {personal_info['location']}")
        if info_strs:
            context_parts.append(f"- 基本信息: {', '.join(info_strs)}")
    
    mbti_features = [f for f in features if f.get("feature_type") == "MBTI" and f.get("confidence", 0) >= 0.6]
    if mbti_features:
        mbti = mbti_features[0]
        context_parts.append(f"- 性格类型(MBTI): {mbti.get('feature_value', '')}（置信度: {mbti.get('confidence', 0):.0%}）")
    
    big_five_features = [f for f in features if f.get("feature_type") == "大五人格" and f.get("confidence", 0) >= 0.6]
    if big_five_features:
        traits = []
        for f in big_five_features[:5]:
            trait_name = f.get("feature_value", "").split(':')[0] if ':' in f.get("feature_value", "") else f.get("feature_value", "")
            traits.append(f"{trait_name}({f.get('confidence', 0):.0%})")
        if traits:
            context_parts.append(f"- 人格特质: {', '.join(traits)}")
    
    behavior_features = [f for f in features if f.get("feature_type") == "行为习惯" and f.get("confidence", 0) >= 0.6]
    if behavior_features:
        habits = [f.get("feature_value", "") for f in behavior_features[:5]]
        context_parts.append(f"- 行为习惯: {', '.join(habits)}")
    
    interest_features = [f for f in features if f.get("feature_type") == "兴趣爱好" and f.get("confidence", 0) >= 0.6]
    if interest_features:
        interests = [f.get("feature_value", "") for f in interest_features[:5]]
        context_parts.append(f"- 兴趣爱好: {', '.join(interests)}")
    
    value_features = [f for f in features if f.get("feature_type") == "价值观" and f.get("confidence", 0) >= 0.6]
    if value_features:
        values = [f.get("feature_value", "") for f in value_features[:3]]
        context_parts.append(f"- 价值观: {', '.join(values)}")
    
    intent_features = [f for f in features if f.get("feature_type") == "潜在想法" and f.get("confidence", 0) >= 0.7]
    if intent_features:
        intents = [f.get("feature_value", "") for f in intent_features[:3]]
        context_parts.append(f"- 潜在需求/想法: {', '.join(intents)}")
    
    emotion_features = [f for f in features if f.get("feature_type") == "情感状态" and f.get("confidence", 0) >= 0.6]
    if emotion_features:
        emotions = [f.get("feature_value", "") for f in emotion_features[:3]]
        context_parts.append(f"- 情感状态: {', '.join(emotions)}")
    
    inferred_features = [f for f in features if f.get("feature_type") in ["推断特征", "推断"] and f.get("confidence", 0) >= 0.6]
    if inferred_features:
        inferred = [f.get("feature_value", "") for f in inferred_features[:3]]
        context_parts.append(f"- 推断特征: {', '.join(inferred)}")
    
    user_context = "\n".join(context_parts) if len(context_parts) > 1 else ""
    
    return f"""你是一个友善、贴心的AI助手，正在与用户进行对话。你已经通过之前的对话了解了这位用户的一些特征信息。

{user_context}

## 个性化回复指南
请根据以上用户画像信息，提供更加贴心、个性化的回复：

1. **结合用户特征做决策建议**：
   - 如果用户在寻求建议或选择，根据用户的性格、价值观、行为习惯给出有倾向性的建议
   - 不要只是列出选项，要结合用户画像给出明确的推荐
   - 例如：如果用户性格保守，在风险选择上应推荐保守选项

2. **自然融入用户特征**：
   - 如果用户有明确的兴趣爱好，可以在相关话题中自然地提及
   - 如果用户有特定的行为习惯，可以理解并尊重这些习惯

3. **情感共鸣**：
   - 根据用户的情感状态和性格特点，调整回复的语气和风格
   - 对于内向型用户，可以更加温和、耐心

4. **保持自然**：
   - 不要生硬地提及"根据你的画像"或"基于你的特征"
   - 让个性化融入回复中，像老朋友一样自然对话

请直接回答用户的问题，给出有倾向性的建议，不要只是中立地分析。"""


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

            use_personalization = _should_use_personalization(request.message)
            
            if use_personalization:
                features = get_user_features_sync(request.user_id)
                system_prompt = _build_personalization_prompt(features, request.message)
            else:
                system_prompt = """你是一个友善的AI助手，正在与用户进行对话。

## 回复要求
1. 直接回答用户的问题
2. 保持回复简洁、自然

请直接回答。"""
            
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

            print(f"\n>>> 保存对话到数据库...")
            print(f"  - 用户ID: {request.user_id}")
            print(f"  - 用户消息: {request.message[:50]}...")
            print(f"  - 助手回复: {display_content[:50]}...")
            print(f"  - 思考内容: {think_content[:50] if think_content else 'None'}...")
            
            save_conversation_sync(request.user_id, "user", request.message, "default", None)
            save_conversation_sync(request.user_id, "assistant", display_content if display_content else "(无回复内容)", "default", think_content)
            print(f">>> 对话保存完成\n")

            if think_content:
                yield f"data: {json.dumps({'type': 'think', 'content': think_content})}\n\n"

            yield f"data: {json.dumps({'type': 'done', 'content': display_content, 'think_content': think_content})}\n\n"

            if request.extract_features:
                import asyncio
                asyncio.create_task(
                    _extract_features_async(request.user_id, request.message, display_content)
                )

        except Exception as e:
            import traceback
            error_msg = str(e)
            print(f"Stream error: {error_msg}")
            print(traceback.format_exc())
            yield f"data: {json.dumps({'type': 'error', 'content': f'错误：{error_msg}'})}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")


async def _extract_features_async(user_id: str, message: str, response: str):
    """异步执行特征提取，不阻塞流式响应"""
    try:
        print(f">>> 开始特征提取...")
        import asyncio
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(
            None, 
            extract_features_sync, 
            user_id, 
            message, 
            response if response else "(无回复内容)"
        )
        print(f">>> 特征提取完成")
    except Exception as e:
        print(f">>> 特征提取失败: {e}")
        import traceback
        print(traceback.format_exc())


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
        
        # 获取用户预测（Top 10）
        predictions = get_user_predictions_sync(user_id)
        
        return {
            "user_id": user_id,
            "features": features,
            "predictions": predictions,
            "summary": {
                "conversation_count": conversation_count,
                "feature_count": len(features),
                "first_conversation": str(time_range[0]) if time_range[0] else None,
                "last_conversation": str(time_range[1]) if time_range[1] else None,
                "big_five": big_five,
                "mbti": mbti,
                "confidence_score": calculate_average_confidence(features)
            },
            "features_by_type": features_by_type
        }
    except Exception as e:
        import traceback
        print(f"获取用户画像失败：{e}")
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/profile/{user_id}/predict")
async def generate_predictions(
    user_id: str,
    force_refresh: bool = False
):
    """生成用户行为预测"""
    from backend.utils.sync_database import get_user_features_sync, get_user_conversations_sync
    from backend.agents.prediction_agent import get_prediction_agent
    from backend.utils.sync_database import save_predictions_sync
    
    try:
        # 如果不强制刷新，先检查是否有缓存的预测
        if not force_refresh:
            cached_result = get_cached_predictions_sync(user_id)
            if cached_result.get("is_valid") and cached_result.get("predictions"):
                return {
                    "predictions": cached_result["predictions"], 
                    "cached": True,
                    "feature_count_changed": cached_result.get("is_feature_count_changed", False)
                }
        
        # 获取特征和对话
        features = get_user_features_sync(user_id)
        conversations = get_user_conversations_sync(user_id, limit=20)
        
        if not features:
            return {"predictions": [], "message": "特征不足，无法生成预测"}
        
        # 使用预测 Agent 生成预测
        agent = get_prediction_agent()
        predictions = await agent.predict_user_behavior(
            user_id=user_id,
            features=features,
            recent_conversations=conversations
        )
        
        # 保存预测到数据库
        if predictions:
            save_predictions_sync(user_id, predictions)
        
        return {"predictions": predictions[:10], "cached": False}
        
    except Exception as e:
        import traceback
        print(f"生成预测失败：{e}")
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
    import re
    mbti_pattern = r'[IE][NS][FT][JP]'
    
    mbti_candidates = []
    for f in features:
        if f.get('feature_type') == 'MBTI':
            value = f.get('feature_value', '')
            confidence = f.get('confidence', 0)
            
            matches = re.findall(mbti_pattern, value.upper())
            if matches:
                for match in matches:
                    mbti_candidates.append((match, confidence))
    
    if mbti_candidates:
        mbti_counts = {}
        for mbti, conf in mbti_candidates:
            if mbti not in mbti_counts:
                mbti_counts[mbti] = {'count': 0, 'total_confidence': 0}
            mbti_counts[mbti]['count'] += 1
            mbti_counts[mbti]['total_confidence'] += conf
        
        best_mbti = max(mbti_counts.items(), 
                       key=lambda x: (x[1]['count'], x[1]['total_confidence']))
        return best_mbti[0]
    
    return None

def calculate_average_confidence(features):
    """计算平均置信度"""
    if not features or len(features) == 0:
        return 0.0
    total = sum(f.get('confidence', 0) for f in features)
    return round(total / len(features), 2)

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


@router.get("/profile/{user_id}/insights")
async def get_profile_insights(user_id: str):
    """获取用户画像洞察：智能提醒"""
    import sqlite3
    from datetime import datetime, timedelta
    
    try:
        conn = sqlite3.connect('C:\\myProject\\MindPeek\\data\\permir.db')
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT feature_type, feature_value, confidence, updated_at, created_at
            FROM features 
            WHERE user_id = ? AND is_active = 1
            ORDER BY updated_at DESC
        """, (user_id,))
        features = cursor.fetchall()
        
        cursor.execute("""
            SELECT content, timestamp, role
            FROM conversations 
            WHERE user_id = ?
            ORDER BY timestamp DESC
            LIMIT 50
        """, (user_id,))
        conversations = cursor.fetchall()
        
        alerts = []
        
        emotion_keywords = {
            "焦虑": ["焦虑", "担心", "紧张", "不安", "压力"],
            "抑郁": ["难过", "沮丧", "郁闷", "失落", "孤独"],
            "愤怒": ["生气", "愤怒", "烦躁", "不满"],
            "快乐": ["开心", "高兴", "愉快", "满足", "幸福"]
        }
        
        recent_emotion_counts = {k: 0 for k in emotion_keywords.keys()}
        
        one_week_ago = datetime.utcnow() - timedelta(days=7)
        
        for conv in conversations:
            content = conv[0].lower() if conv[0] else ""
            timestamp = conv[1]
            try:
                conv_time = datetime.fromisoformat(str(timestamp).replace('Z', '+00:00').replace('+00:00', ''))
            except:
                conv_time = datetime.utcnow()
            
            for emotion, keywords in emotion_keywords.items():
                for kw in keywords:
                    if kw in content:
                        if conv_time > one_week_ago:
                            recent_emotion_counts[emotion] += 1
        
        for emotion, count in recent_emotion_counts.items():
            if count >= 3:
                if emotion in ["焦虑", "抑郁", "愤怒"]:
                    alerts.append({
                        "type": "emotion_alert",
                        "level": "warning" if count < 5 else "serious",
                        "title": f"检测到{emotion}情绪倾向",
                        "message": f"近一周内检测到{count}次{emotion}相关表达，建议关注心理健康",
                        "icon": "warning"
                    })
            elif emotion == "快乐" and count >= 5:
                alerts.append({
                    "type": "emotion_positive",
                    "level": "info",
                    "title": "情绪状态良好",
                    "message": f"近期情绪积极，继续保持！",
                    "icon": "success"
                })
        
        total_features = len(features)
        
        conn.close()
        
        return {
            "alerts": alerts[:5],
            "stats": {
                "total_features": total_features,
                "recent_emotions": recent_emotion_counts
            }
        }
        
    except Exception as e:
        import traceback
        print(f"获取画像洞察失败：{e}")
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))
