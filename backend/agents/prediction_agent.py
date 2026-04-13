"""
用户行为预测 Agent
基于用户历史特征和行为模式，预测用户未来最有可能的行为或想法
"""
import asyncio
from datetime import datetime
from typing import List, Dict, Any
from backend.services.llm_provider import LLMProviderFactory
from backend.core.config import config_manager


class PredictionAgent:
    """用户行为预测 Agent"""
    
    def __init__(self):
        default_provider = config_manager.get_default_provider()
        self.llm = LLMProviderFactory.get_provider(default_provider)
    
    async def predict_user_behavior(
        self,
        user_id: str,
        features: List[Dict[str, Any]],
        recent_conversations: List[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        预测用户未来最有可能的行为或想法
        
        Args:
            user_id: 用户 ID
            features: 用户特征列表
            recent_conversations: 最近对话记录（可选）
            
        Returns:
            Top10 预测结果列表，按可能性排序
        """
        # 构建特征摘要
        feature_summary = self._build_feature_summary(features)
        
        # 构建对话摘要（如果有）
        conversation_summary = ""
        if recent_conversations:
            conversation_summary = self._build_conversation_summary(recent_conversations)
        
        # 构建预测提示
        prompt = self._build_prediction_prompt(
            user_id,
            feature_summary,
            conversation_summary
        )
        
        # 调用 LLM 进行预测
        try:
            response = await self.llm.chat([{"role": "user", "content": prompt}])
            predictions = self._parse_predictions(response)
            if predictions:
                return predictions[:10]  # 返回 Top10
            else:
                print("LLM 返回空预测")
                return []
        except Exception as e:
            print(f"LLM 预测失败：{e}")
            return []
    
    def _build_feature_summary(self, features: List[Dict[str, Any]]) -> str:
        """构建特征摘要"""
        if not features:
            return "暂无特征数据"
        
        # 按类型分组
        features_by_type = {}
        for f in features:
            ftype = f.get('feature_type', '未知')
            if ftype not in features_by_type:
                features_by_type[ftype] = []
            features_by_type[ftype].append({
                'value': f.get('feature_value', ''),
                'confidence': f.get('confidence', 0)
            })
        
        summary_lines = []
        for ftype, flist in features_by_type.items():
            values = [f['value'] for f in flist[:3]]  # 每个类型最多取 3 个
            avg_confidence = sum(f['confidence'] for f in flist) / len(flist)
            summary_lines.append(
                f"- {ftype}：{', '.join(values)} (平均置信度：{avg_confidence:.0%})"
            )
        
        return "\n".join(summary_lines)
    
    def _build_conversation_summary(self, conversations: List[Dict[str, Any]]) -> str:
        """构建对话摘要"""
        if not conversations:
            return ""
        
        # 取最近 5 轮对话
        recent = conversations[-5:]
        lines = []
        for conv in recent:
            role = conv.get('role', '')
            content = conv.get('content', '')[:100]  # 限制长度
            lines.append(f"{role}: {content}")
        
        return "\n".join(lines)
    
    def _build_prediction_prompt(
        self,
        user_id: str,
        feature_summary: str,
        conversation_summary: str
    ) -> str:
        """构建预测提示"""
        prompt = f"""你是一个专业的用户行为预测专家。请根据用户的特征和历史对话，预测用户未来最有可能的行为或想法。

## 用户信息
用户 ID: {user_id}

## 用户特征
{feature_summary}

## 最近对话
{conversation_summary if conversation_summary else "无对话记录"}

## 预测要求
1. 基于用户的性格特点、行为习惯、价值观等特征进行推断
2. 考虑用户的历史行为模式
3. 预测应该具体、可观察、可验证
4. 涵盖不同方面：行为、想法、情感、决策等
5. 每个预测都要说明推断依据和可能性评估

## 输出格式（严格 JSON 数组）
[
    {{
        "prediction": "预测内容（简洁明了）",
        "category": "类别（行为/想法/情感/决策/其他）",
        "confidence": 0.0-1.0（可能性评分）",
        "reasoning": "推断依据（引用具体特征）",
        "timeframe": "时间范围（短期 1-7 天/中期 1-4 周/长期 1-3 月）",
        "observable_signals": ["可观察的信号 1", "信号 2"]
    }}
]

请预测 15-20 个可能的行为或想法，按可能性从高到低排序。"""
        
        return prompt
    
    def _parse_predictions(self, response: str) -> List[Dict[str, Any]]:
        """解析 LLM 返回的预测结果"""
        import json
        
        try:
            # 提取 JSON 部分
            start = response.find('[')
            end = response.rfind(']') + 1
            if start == -1 or end == 0:
                print("未找到 JSON 数组")
                return []
            
            json_str = response[start:end]
            predictions = json.loads(json_str)
            
            # 验证和清理数据
            validated = []
            for p in predictions:
                if not isinstance(p, dict):
                    continue
                
                prediction = {
                    'prediction': p.get('prediction', ''),
                    'category': p.get('category', '其他'),
                    'confidence': float(p.get('confidence', 0.5)),
                    'reasoning': p.get('reasoning', ''),
                    'timeframe': p.get('timeframe', '中期'),
                    'observable_signals': p.get('observable_signals', []),
                    'created_at': datetime.utcnow().isoformat()
                }
                
                # 确保必要字段存在
                if prediction['prediction']:
                    validated.append(prediction)
            
            # 按置信度排序
            validated.sort(key=lambda x: x['confidence'], reverse=True)
            
            return validated
            
        except json.JSONDecodeError as e:
            print(f"解析预测结果失败：{e}")
            return []
        except Exception as e:
            print(f"处理预测结果失败：{e}")
            return []


# 全局实例
_prediction_agent = None

def get_prediction_agent() -> PredictionAgent:
    """获取预测 Agent 实例"""
    global _prediction_agent
    if _prediction_agent is None:
        _prediction_agent = PredictionAgent()
    return _prediction_agent
