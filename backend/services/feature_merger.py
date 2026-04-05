"""
特征智能合并服务 - 用于识别和合并相似特征
支持规则优先 + LLM 兜底的混合智能模式
"""
import re
import asyncio
from typing import List, Dict, Tuple, Optional, Set
from difflib import SequenceMatcher
from datetime import datetime


class FeatureMerger:
    """特征智能合并器 - 规则 + LLM 混合模式"""

    def __init__(self, use_llm: bool = True):
        self.synonyms = self._load_synonyms()
        self.abbreviations = self._load_abbreviations()
        self.conflicts = self._load_conflicts()
        self.normalizers = self._load_normalizers()
        self.use_llm = use_llm
        self._llm_provider = None
        self._llm_cache = {}
        self._llm_available = None

    def _load_synonyms(self) -> Dict[str, List[str]]:
        """加载同义词库"""
        return {
            "喜欢": ["喜爱", "爱好", "热爱", "偏好", "乐于", "爱", "沉迷", "着迷"],
            "不喜欢": ["讨厌", "厌恶", "反感", "不爱", "避开"],
            "阅读": ["看书", "读书", "阅览"],
            "运动": ["锻炼", "健身", "体育"],
            "音乐": ["听歌", "听音乐", "欣赏音乐"],
            "游戏": ["玩游戏", "打游戏"],
            "电影": ["看电影", "观影"],
            "旅行": ["旅游", "出行", "游玩"],
            "烹饪": ["做饭", "下厨", "做菜"],
            "学习": ["进修", "充电", "自我提升"],
            "工作": ["上班", "职业"],
            "社交": ["交朋友", "社交活动", "与人交往"],
            "内向": ["不爱说话", "安静", "害羞"],
            "外向": ["开朗", "活泼", "爱说话"],
            "熬夜": ["夜猫子", "晚睡"],
            "早起": ["早睡早起", "清晨"],
        }

    def _load_abbreviations(self) -> Dict[str, List[str]]:
        """加载缩写词库"""
        return {
            "人工智能": ["AI", "ai"],
            "机器学习": ["ML", "ml"],
            "深度学习": ["DL", "dl"],
            "自然语言处理": ["NLP", "nlp"],
            "计算机视觉": ["CV", "cv"],
        }

    def _load_conflicts(self) -> Dict[str, Set[str]]:
        """加载冲突特征库 - 互斥的特征对"""
        return {
            "内向型": {"外向型", "外向", "外向性较高"},
            "外向型": {"内向型", "内向", "内向性较高"},
            "INTP": {"INTJ", "INFP", "INFJ", "ENTP", "ENTJ", "ENFP", "ENFJ", 
                     "ISTP", "ISTJ", "ISFP", "ISFJ", "ESTP", "ESTJ", "ESFP", "ESFJ"},
            "INFP": {"INTJ", "INTP", "INFJ", "ENTP", "ENTJ", "ENFP", "ENFJ",
                     "ISTP", "ISTJ", "ISFP", "ISFJ", "ESTP", "ESTJ", "ESFP", "ESFJ"},
            "INTJ": {"INTP", "INFP", "INFJ", "ENTP", "ENTJ", "ENFP", "ENFJ",
                     "ISTP", "ISTJ", "ISFP", "ISFJ", "ESTP", "ESTJ", "ESFP", "ESFJ"},
            "INFJ": {"INTJ", "INTP", "INFP", "ENTP", "ENTJ", "ENFP", "ENFJ",
                     "ISTP", "ISTJ", "ISFP", "ISFJ", "ESTP", "ESTJ", "ESFP", "ESFJ"},
            "ENTP": {"INTJ", "INTP", "INFP", "INFJ", "ENTJ", "ENFP", "ENFJ",
                     "ISTP", "ISTJ", "ISFP", "ISFJ", "ESTP", "ESTJ", "ESFP", "ESFJ"},
            "ENTJ": {"INTJ", "INTP", "INFP", "INFJ", "ENTP", "ENFP", "ENFJ",
                     "ISTP", "ISTJ", "ISFP", "ISFJ", "ESTP", "ESTJ", "ESFP", "ESFJ"},
            "ENFP": {"INTJ", "INTP", "INFP", "INFJ", "ENTP", "ENTJ", "ENFJ",
                     "ISTP", "ISTJ", "ISFP", "ISFJ", "ESTP", "ESTJ", "ESFP", "ESFJ"},
            "ENFJ": {"INTJ", "INTP", "INFP", "INFJ", "ENTP", "ENTJ", "ENFP",
                     "ISTP", "ISTJ", "ISFP", "ISFJ", "ESTP", "ESTJ", "ESFP", "ESFJ"},
            "ISTP": {"INTJ", "INTP", "INFP", "INFJ", "ENTP", "ENTJ", "ENFP", "ENFJ",
                     "ISTJ", "ISFP", "ISFJ", "ESTP", "ESTJ", "ESFP", "ESFJ"},
            "ISTJ": {"INTJ", "INTP", "INFP", "INFJ", "ENTP", "ENTJ", "ENFP", "ENFJ",
                     "ISTP", "ISFP", "ISFJ", "ESTP", "ESTJ", "ESFP", "ESFJ"},
            "ISFP": {"INTJ", "INTP", "INFP", "INFJ", "ENTP", "ENTJ", "ENFP", "ENFJ",
                     "ISTP", "ISTJ", "ISFJ", "ESTP", "ESTJ", "ESFP", "ESFJ"},
            "ISFJ": {"INTJ", "INTP", "INFP", "INFJ", "ENTP", "ENTJ", "ENFP", "ENFJ",
                     "ISTP", "ISTJ", "ISFP", "ESTP", "ESTJ", "ESFP", "ESFJ"},
            "ESTP": {"INTJ", "INTP", "INFP", "INFJ", "ENTP", "ENTJ", "ENFP", "ENFJ",
                     "ISTP", "ISTJ", "ISFP", "ISFJ", "ESTJ", "ESFP", "ESFJ"},
            "ESTJ": {"INTJ", "INTP", "INFP", "INFJ", "ENTP", "ENTJ", "ENFP", "ENFJ",
                     "ISTP", "ISTJ", "ISFP", "ISFJ", "ESTP", "ESFP", "ESFJ"},
            "ESFP": {"INTJ", "INTP", "INFP", "INFJ", "ENTP", "ENTJ", "ENFP", "ENFJ",
                     "ISTP", "ISTJ", "ISFP", "ISFJ", "ESTP", "ESTJ", "ESFJ"},
            "ESFJ": {"INTJ", "INTP", "INFP", "INFJ", "ENTP", "ENTJ", "ENFP", "ENFJ",
                     "ISTP", "ISTJ", "ISFP", "ISFJ", "ESTP", "ESTJ", "ESFP"},
            "思考型": {"情感型"},
            "情感型": {"思考型"},
            "判断型": {"感知型"},
            "感知型": {"判断型"},
            "直觉型": {"感觉型"},
            "感觉型": {"直觉型"},
        }

    def _load_normalizers(self) -> Dict[str, Dict]:
        """加载特征标准化规则"""
        return {
            "MBTI": {
                "patterns": [
                    (r"可能倾向于内向类型[（(]如\s*(\w{4})\s*[、,]\s*(\w{4})\s*[)）]", "倾向内向"),
                    (r"可能倾向于外向型", "倾向外向"),
                    (r"可能倾向于内向型", "倾向内向"),
                    (r"可能倾向于内向或感知觉类型", "倾向内向"),
                    (r"(\w{4})\s*或\s*(\w{4})", "MBTI候选"),
                    (r"(\w{4})", "MBTI确定"),
                ],
                "normalize": self._normalize_mbti
            }
        }

    def _normalize_mbti(self, value: str) -> Tuple[str, float]:
        """标准化 MBTI 特征值"""
        value = value.strip()
        
        mbti_types = ["INTJ", "INTP", "INFJ", "INFP", "ENTJ", "ENTP", "ENFJ", "ENFP",
                      "ISTJ", "ISTP", "ISFJ", "ISFP", "ESTJ", "ESTP", "ESFJ", "ESFP"]
        
        found_types = []
        for mbti in mbti_types:
            if mbti in value.upper():
                found_types.append(mbti)
        
        if len(found_types) == 1:
            return found_types[0], 0.9
        
        if len(found_types) == 2:
            sorted_types = sorted(found_types)
            return f"{sorted_types[0]}/{sorted_types[1]}", 0.7
        
        if "内向" in value or "introvert" in value.lower():
            return "倾向内向", 0.6
        if "外向" in value or "extravert" in value.lower():
            return "倾向外向", 0.6
        
        return value, 0.5

    def normalize_feature(self, feature_type: str, feature_value: str) -> Tuple[str, float]:
        """标准化特征值"""
        normalizer = self.normalizers.get(feature_type)
        if normalizer:
            return normalizer["normalize"](feature_value)
        return feature_value, 1.0

    def check_conflict(self, feature1: Dict, feature2: Dict) -> Tuple[bool, str]:
        """
        检查两个特征是否冲突
        
        Returns:
            (是否冲突, 冲突原因)
        """
        type1 = feature1.get("feature_type", "")
        type2 = feature2.get("feature_type", "")
        val1 = feature1.get("feature_value", "")
        val2 = feature2.get("feature_value", "")
        
        if type1 != type2:
            return False, ""
        
        val1_lower = val1.lower()
        val2_lower = val2.lower()
        
        if type1 == "MBTI":
            introvert_types = ["INTJ", "INTP", "INFJ", "INFP", "ISTJ", "ISTP", "ISFJ", "ISFP"]
            extravert_types = ["ENTJ", "ENTP", "ENFJ", "ENFP", "ESTJ", "ESTP", "ESFJ", "ESFP"]
            
            has_introvert_mbti = any(mbti in val1_upper for mbti in introvert_types for val1_upper in [val1.upper()])
            has_extravert_mbti = any(mbti in val1_upper for mbti in extravert_types for val1_upper in [val1.upper()])
            has_introvert_mbti2 = any(mbti in val2_upper for mbti in introvert_types for val2_upper in [val2.upper()])
            has_extravert_mbti2 = any(mbti in val2_upper for mbti in extravert_types for val2_upper in [val2.upper()])
            
            has_introvert_tendency = "内向" in val1 or has_introvert_mbti
            has_extravert_tendency = "外向" in val1 or has_extravert_mbti
            has_introvert_tendency2 = "内向" in val2 or has_introvert_mbti2
            has_extravert_tendency2 = "外向" in val2 or has_extravert_mbti2
            
            if has_introvert_tendency and has_extravert_tendency2:
                return True, f"'{val1}' 与 '{val2}' 存在冲突（内向型 vs 外向型）"
            if has_extravert_tendency and has_introvert_tendency2:
                return True, f"'{val1}' 与 '{val2}' 存在冲突（外向型 vs 内向型）"
            
            for mbti in introvert_types + extravert_types:
                if mbti in val1.upper():
                    for conflict in self.conflicts.get(mbti, []):
                        if conflict in val2.upper():
                            return True, f"'{val1}' 与 '{val2}' 存在冲突（{mbti} vs {conflict}）"
        
        for key, conflicts in self.conflicts.items():
            key_lower = key.lower()
            if key_lower in val1_lower:
                for conflict in conflicts:
                    if conflict.lower() in val2_lower:
                        return True, f"'{val1}' 与 '{val2}' 存在冲突（{key} vs {conflict}）"
            if key_lower in val2_lower:
                for conflict in conflicts:
                    if conflict.lower() in val1_lower:
                        return True, f"'{val2}' 与 '{val1}' 存在冲突（{key} vs {conflict}）"
        
        return False, ""

    def _get_llm_provider(self):
        """获取 LLM 提供者"""
        if self._llm_available is False:
            return None
        
        if self._llm_provider is None and self.use_llm:
            try:
                from .llm_provider import LLMProviderFactory
                from ..core.config import config_manager
                default_provider = config_manager.get_default_provider()
                self._llm_provider = LLMProviderFactory.get_provider(default_provider)
                self._llm_available = True
            except Exception as e:
                print(f"LLM 提供者初始化失败: {e}")
                self._llm_provider = None
                self._llm_available = False
        return self._llm_provider

    def _llm_check_conflict(self, feature1: Dict, feature2: Dict) -> Tuple[bool, str]:
        """使用 LLM 智能判断两个特征是否冲突"""
        if not self.use_llm or self._llm_available is False:
            return False, ""
        
        llm = self._get_llm_provider()
        if not llm:
            return False, ""
        
        type1 = feature1.get("feature_type", "")
        val1 = feature1.get("feature_value", "")
        val2 = feature2.get("feature_value", "")
        
        cache_key = f"conflict:{type1}:{val1}|{val2}"
        if cache_key in self._llm_cache:
            return self._llm_cache[cache_key]
        
        prompt = f"""你是一个特征冲突检测专家。请判断以下两个特征值是否存在语义冲突。

特征类型: {type1}
特征值1: {val1}
特征值2: {val2}

请分析：
1. 这两个特征值是否描述的是同一个维度/属性？
2. 如果是，它们的值是否存在矛盾？

请用以下 JSON 格式回复：
{{"is_conflict": true/false, "reason": "冲突原因（如果有）", "confidence": 0.0-1.0}}

注意：
- 只有当两个值确实存在逻辑矛盾时才判断为冲突
- 相似但不完全相同的值不算冲突（如"喜欢阅读"和"喜欢看书"）
- 不同程度描述不算冲突（如"偶尔运动"和"经常运动"可以共存）
- 只回复 JSON，不要其他内容"""

        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future = executor.submit(
                        asyncio.run,
                        llm.chat([{"role": "user", "content": prompt}])
                    )
                    response = future.result(timeout=10)
            else:
                response = loop.run_until_complete(
                    llm.chat([{"role": "user", "content": prompt}])
                )
            
            import json
            response = response.strip()
            if response.startswith("```"):
                response = re.sub(r'^```(?:json)?\s*', '', response)
                response = re.sub(r'\s*```$', '', response)
            
            result = json.loads(response)
            is_conflict = result.get("is_conflict", False)
            reason = result.get("reason", "")
            
            self._llm_cache[cache_key] = (is_conflict, reason)
            return is_conflict, reason
            
        except Exception as e:
            self._llm_available = False
            return False, ""

    def _llm_check_similarity(self, val1: str, val2: str, feature_type: str = "") -> Tuple[bool, float]:
        """使用 LLM 智能判断两个特征值是否相似/重复"""
        if not self.use_llm or self._llm_available is False:
            return False, 0.0
        
        llm = self._get_llm_provider()
        if not llm:
            return False, 0.0
        
        cache_key = f"similarity:{feature_type}:{val1}|{val2}"
        if cache_key in self._llm_cache:
            return self._llm_cache[cache_key]
        
        prompt = f"""你是一个特征相似度判断专家。请判断以下两个特征值是否表达相同或非常相似的含义。

特征类型: {feature_type}
特征值1: {val1}
特征值2: {val2}

请分析这两个值是否在语义上等价或高度相似。

请用以下 JSON 格式回复：
{{"is_similar": true/false, "similarity": 0.0-1.0, "reason": "判断理由"}}

注意：
- similarity 应该反映语义相似程度
- 同义词、不同表达方式应判断为相似
- 只有回复 JSON，不要其他内容"""

        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future = executor.submit(
                        asyncio.run,
                        llm.chat([{"role": "user", "content": prompt}])
                    )
                    response = future.result(timeout=10)
            else:
                response = loop.run_until_complete(
                    llm.chat([{"role": "user", "content": prompt}])
                )
            
            import json
            response = response.strip()
            if response.startswith("```"):
                response = re.sub(r'^```(?:json)?\s*', '', response)
                response = re.sub(r'\s*```$', '', response)
            
            result = json.loads(response)
            is_similar = result.get("is_similar", False)
            similarity = result.get("similarity", 0.0)
            
            self._llm_cache[cache_key] = (is_similar, similarity)
            return is_similar, similarity
            
        except Exception as e:
            self._llm_available = False
            return False, 0.0

    def _llm_merge_values(self, values: List[str], feature_type: str, weights: List[float] = None) -> Tuple[str, float]:
        """使用 LLM 智能合并多个特征值"""
        if not self.use_llm or self._llm_available is False:
            if values:
                return values[0], 0.5
            return "", 0.0
        
        llm = self._get_llm_provider()
        if not llm or len(values) <= 1:
            if values:
                return values[0], 0.5
            return "", 0.0
        
        cache_key = f"merge:{feature_type}:{','.join(values)}"
        if cache_key in self._llm_cache:
            return self._llm_cache[cache_key]
        
        values_desc = "\n".join([f"- {v}" for v in values])
        weights_desc = ""
        if weights:
            weights_desc = "\n权重信息:\n" + "\n".join([f"- {v}: {w:.2f}" for v, w in zip(values, weights)])
        
        prompt = f"""你是一个特征值合并专家。请将以下多个特征值合并为一个最准确的值。

特征类型: {feature_type}
特征值列表:
{values_desc}
{weights_desc}

请分析这些特征值，并生成一个最准确、最全面的合并结果。

请用以下 JSON 格式回复：
{{"merged_value": "合并后的值", "confidence": 0.0-1.0, "reasoning": "合并理由"}}

注意：
- 对于数值型特征，考虑加权平均
- 对于描述型特征，选择最准确、最全面的表述
- 如果有矛盾，选择权重更高或更合理的值
- 只回复 JSON，不要其他内容"""

        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future = executor.submit(
                        asyncio.run,
                        llm.chat([{"role": "user", "content": prompt}])
                    )
                    response = future.result(timeout=15)
            else:
                response = loop.run_until_complete(
                    llm.chat([{"role": "user", "content": prompt}])
                )
            
            import json
            response = response.strip()
            if response.startswith("```"):
                response = re.sub(r'^```(?:json)?\s*', '', response)
                response = re.sub(r'\s*```$', '', response)
            
            result = json.loads(response)
            merged_value = result.get("merged_value", values[0])
            confidence = result.get("confidence", 0.5)
            
            self._llm_cache[cache_key] = (merged_value, confidence)
            return merged_value, confidence
            
        except Exception as e:
            print(f"LLM 特征合并失败: {e}")
            return values[0], 0.5

    def check_conflict_with_llm(self, feature1: Dict, feature2: Dict) -> Tuple[bool, str]:
        """
        检查两个特征是否冲突（规则优先 + LLM 兜底）
        
        Returns:
            (是否冲突, 冲突原因)
        """
        is_conflict, reason = self.check_conflict(feature1, feature2)
        
        if is_conflict:
            return True, reason
        
        if self.use_llm:
            type1 = feature1.get("feature_type", "")
            type2 = feature2.get("feature_type", "")
            
            if type1 == type2:
                val1 = feature1.get("feature_value", "")
                val2 = feature2.get("feature_value", "")
                
                if val1 and val2 and val1 != val2:
                    llm_conflict, llm_reason = self._llm_check_conflict(feature1, feature2)
                    if llm_conflict:
                        return True, f"[LLM判断] {llm_reason}"
        
        return False, ""

    def detect_conflicts(self, features: List[Dict]) -> List[Tuple[Dict, Dict, str]]:
        """
        检测特征列表中的冲突
        
        Returns:
            冲突特征对列表 (特征1, 特征2, 冲突原因)
        """
        conflicts = []
        n = len(features)
        
        for i in range(n):
            for j in range(i + 1, n):
                feat1 = features[i]
                feat2 = features[j]
                
                is_conflict, reason = self.check_conflict(feat1, feat2)
                if is_conflict:
                    conflicts.append((feat1, feat2, reason))
        
        return conflicts

    def normalize_text(self, text: str) -> str:
        """标准化文本"""
        text = text.lower().strip()
        text = re.sub(r'[^\w\s]', '', text)
        text = re.sub(r'\s+', ' ', text)
        return text

    def calculate_similarity(self, str1: str, str2: str) -> float:
        """计算两个字符串的相似度"""
        str1_norm = self.normalize_text(str1)
        str2_norm = self.normalize_text(str2)
        
        if str1_norm == str2_norm:
            return 1.0
        
        return SequenceMatcher(None, str1_norm, str2_norm).ratio()

    def check_synonym_match(self, str1: str, str2: str) -> Tuple[bool, float]:
        """检查是否是同义词匹配"""
        str1_norm = self.normalize_text(str1)
        str2_norm = self.normalize_text(str2)
        
        for main_word, synonyms in self.synonyms.items():
            all_words = [main_word] + synonyms
            str1_in = str1_norm in all_words or any(word in str1_norm for word in all_words)
            str2_in = str2_norm in all_words or any(word in str2_norm for word in all_words)
            
            if str1_in and str2_in:
                return True, 0.9
        
        return False, 0.0

    def check_abbreviation_match(self, str1: str, str2: str) -> Tuple[bool, float]:
        """检查是否是缩写词匹配"""
        str1_norm = self.normalize_text(str1)
        str2_norm = self.normalize_text(str2)
        
        for main_word, abbreviations in self.abbreviations.items():
            all_words = [main_word.lower()] + [abbr.lower() for abbr in abbreviations]
            str1_in = str1_norm in all_words or any(word in str1_norm for word in all_words)
            str2_in = str2_norm in all_words or any(word in str2_norm for word in all_words)
            
            if str1_in and str2_in:
                return True, 0.95
        
        return False, 0.0

    def find_best_match(
        self, 
        new_feature: str, 
        existing_features: List[Dict],
        feature_type: Optional[str] = None,
        threshold: float = 0.7
    ) -> Tuple[Optional[Dict], float]:
        """
        在现有特征中找到最佳匹配（规则优先 + LLM 兜底）
        
        Args:
            new_feature: 新特征值
            existing_features: 现有特征列表
            feature_type: 可选的特征类型筛选
            threshold: 相似度阈值
            
        Returns:
            (最佳匹配的特征, 相似度)
        """
        best_match = None
        best_score = 0.0
        
        for feature in existing_features:
            if feature_type and feature.get("feature_type") != feature_type:
                continue
            
            existing_value = feature.get("feature_value", "")
            
            is_synonym, syn_score = self.check_synonym_match(new_feature, existing_value)
            if is_synonym and syn_score > best_score:
                best_match = feature
                best_score = syn_score
                continue
            
            is_abbrev, abbrev_score = self.check_abbreviation_match(new_feature, existing_value)
            if is_abbrev and abbrev_score > best_score:
                best_match = feature
                best_score = abbrev_score
                continue
            
            similarity = self.calculate_similarity(new_feature, existing_value)
            if similarity > best_score and similarity >= threshold:
                best_match = feature
                best_score = similarity
        
        if best_score >= threshold:
            return best_match, best_score
        
        if self.use_llm and self._llm_available is not False and len(existing_features) > 0:
            for feature in existing_features[:5]:
                if feature_type and feature.get("feature_type") != feature_type:
                    continue
                existing_value = feature.get("feature_value", "")
                is_similar, llm_score = self._llm_check_similarity(
                    new_feature, existing_value, feature_type or ""
                )
                if is_similar and llm_score > best_score:
                    best_match = feature
                    best_score = llm_score
                    if best_score >= threshold:
                        break
        
        return best_match, best_score

    def merge_features(
        self,
        existing_feature: Dict,
        new_feature_value: str,
        confidence: float = 0.8
    ) -> Dict:
        """
        合并两个特征
        
        Args:
            existing_feature: 现有特征
            new_feature_value: 新特征值
            confidence: 新特征的置信度
            
        Returns:
            合并后的特征
        """
        from datetime import datetime
        
        existing_confidence = existing_feature.get("confidence", 0.5)
        new_confidence = (existing_confidence + confidence) / 2
        
        existing_notes = existing_feature.get("notes", "")
        if existing_notes:
            existing_notes += f"\n相似表达: {new_feature_value}"
        else:
            existing_notes = f"相似表达: {new_feature_value}"
        
        return {
            **existing_feature,
            "confidence": new_confidence,
            "notes": existing_notes,
            "updated_at": datetime.utcnow()
        }

    def detect_duplicates(
        self,
        features: List[Dict],
        threshold: float = 0.75
    ) -> List[Tuple[Dict, Dict, float]]:
        """
        检测特征列表中的重复项
        
        Args:
            features: 特征列表
            threshold: 相似度阈值
            
        Returns:
            重复特征对列表 (特征1, 特征2, 相似度)
        """
        duplicates = []
        n = len(features)
        
        for i in range(n):
            for j in range(i + 1, n):
                feat1 = features[i]
                feat2 = features[j]
                
                if feat1.get("feature_type") != feat2.get("feature_type"):
                    continue
                
                val1 = feat1.get("feature_value", "")
                val2 = feat2.get("feature_value", "")
                
                similarity = self.calculate_similarity(val1, val2)
                if similarity >= threshold:
                    duplicates.append((feat1, feat2, similarity))
        
        return duplicates

    def deduplicate_features(self, features: List[Dict], threshold: float = 0.75) -> List[Dict]:
        """
        去重特征列表，保留置信度最高的（规则 + LLM 混合模式）
        
        Args:
            features: 特征列表
            threshold: 相似度阈值
            
        Returns:
            去重后的特征列表
        """
        if not features:
            return []
        
        result = []
        used_indices = set()
        
        sorted_features = sorted(features, key=lambda x: x.get("confidence", 0), reverse=True)
        
        for i, feat in enumerate(sorted_features):
            if i in used_indices:
                continue
            
            result.append(feat)
            
            for j in range(i + 1, len(sorted_features)):
                if j in used_indices:
                    continue
                
                other = sorted_features[j]
                
                if feat.get("feature_type") != other.get("feature_type"):
                    continue
                
                val1 = feat.get("feature_value", "")
                val2 = other.get("feature_value", "")
                
                similarity = self.calculate_similarity(val1, val2)
                is_duplicate = similarity >= threshold
                
                if not is_duplicate and self.use_llm and similarity >= 0.5:
                    llm_similar, llm_score = self._llm_check_similarity(
                        val1, val2, feat.get("feature_type", "")
                    )
                    if llm_similar:
                        is_duplicate = True
                        print(f"[LLM] 检测到相似特征: '{val1}' ≈ '{val2}' (相似度: {llm_score:.2f})")
                
                if is_duplicate:
                    used_indices.add(j)
        
        return result

    def resolve_conflicts(self, features: List[Dict]) -> List[Dict]:
        """
        解决特征冲突，保留置信度最高的（规则 + LLM 混合模式）
        
        Args:
            features: 特征列表
            
        Returns:
            解决冲突后的特征列表
        """
        if not features:
            return []
        
        result = []
        used_indices = set()
        
        sorted_features = sorted(features, key=lambda x: x.get("confidence", 0), reverse=True)
        
        for i, feat in enumerate(sorted_features):
            if i in used_indices:
                continue
            
            result.append(feat)
            
            for j in range(i + 1, len(sorted_features)):
                if j in used_indices:
                    continue
                
                other = sorted_features[j]
                
                is_conflict, reason = self.check_conflict_with_llm(feat, other)
                if is_conflict:
                    print(f"特征冲突已解决：{reason}，保留置信度较高的 '{feat.get('feature_value')}'")
                    used_indices.add(j)
        
        return result

    def clean_features(self, features: List[Dict]) -> List[Dict]:
        """
        清理特征列表：去重 + 解决冲突 + 同类型合并
        
        Args:
            features: 原始特征列表
            
        Returns:
            清理后的特征列表
        """
        features = self.deduplicate_features(features)
        features = self.resolve_conflicts(features)
        features = self.merge_all_features_comprehensively(features)
        return features

    def _extract_numeric_value(self, value: str) -> Optional[float]:
        """从特征值中提取数值（仅当整个值是纯数字或数字+单位时）"""
        import re
        value = str(value).strip()
        
        if re.match(r'^\d+(?:\.\d+)?$', value):
            return float(value)
        
        if re.match(r'^\d+(?:\.\d+)?\s*[%％]?$', value):
            match = re.match(r'^(\d+(?:\.\d+)?)', value)
            if match:
                return float(match.group(1))
        
        return None

    def _get_level_value(self, value: str) -> Optional[int]:
        """将描述性等级转换为数值"""
        value_lower = value.lower()
        level_map = {
            "极低": 10, "非常低": 10, "很低": 15,
            "低": 20, "较低": 30, "偏低": 30,
            "中等": 50, "中等偏下": 40, "中等偏上": 60,
            "较高": 70, "偏高": 70,
            "高": 80, "较高": 75,
            "极高": 90, "非常高": 90, "很高": 85,
        }
        for key, val in level_map.items():
            if key in value_lower:
                return val
        return None

    def _calculate_time_weight(self, created_at: str) -> float:
        """计算时间权重，越近的权重越高"""
        from datetime import datetime, timedelta
        try:
            if created_at:
                feature_time = datetime.strptime(created_at, "%Y-%m-%d %H:%M:%S.%f")
            else:
                return 0.5
            now = datetime.now()
            days_diff = (now - feature_time).days
            
            if days_diff <= 1:
                return 1.0
            elif days_diff <= 7:
                return 0.9
            elif days_diff <= 30:
                return 0.7
            elif days_diff <= 90:
                return 0.5
            else:
                return 0.3
        except:
            return 0.5

    def _calculate_source_weight(self, feature: Dict) -> float:
        """计算来源权重：用户直接表述 > 推理 > 无来源"""
        source_message = feature.get("source_message")
        reasoning = feature.get("reasoning")
        
        if source_message and source_message.strip():
            return 1.0
        elif reasoning and reasoning.strip():
            return 0.7
        else:
            return 0.5

    def _calculate_total_weight(self, feature: Dict) -> float:
        """计算综合权重 = 来源权重 × 时间权重 × 置信度"""
        source_weight = self._calculate_source_weight(feature)
        time_weight = self._calculate_time_weight(feature.get("created_at", ""))
        confidence = feature.get("confidence", 0.5)
        
        return source_weight * time_weight * confidence

    def _parse_dimension_value(self, value: str) -> Tuple[Optional[str], Optional[float], Optional[int]]:
        """
        解析带维度的特征值，如 "外向性：65" -> ("外向性", 65, None)
        
        Returns:
            (维度名, 数值, 等级数值)
        """
        import re
        
        dimension_patterns = [
            (r'外向性[：:]\s*(\d+)', '外向性'),
            (r'开放性[：:]\s*(\d+)', '开放性'),
            (r'尽责性[：:]\s*(\d+)', '尽责性'),
            (r'宜人性[：:]\s*(\d+)', '宜人性'),
            (r'神经质[：:]\s*(\d+)', '神经质'),
        ]
        
        for pattern, dim_name in dimension_patterns:
            match = re.search(pattern, value)
            if match:
                return (dim_name, float(match.group(1)), None)
        
        level_map = {
            "外向性较高": ("外向性", 70),
            "外向性较低": ("外向性", 30),
            "外向性高": ("外向性", 80),
            "外向性低": ("外向性", 20),
            "开放性较高": ("开放性", 70),
            "开放性较低": ("开放性", 30),
            "尽责性较高": ("尽责性", 70),
            "尽责性较低": ("尽责性", 30),
            "宜人性较高": ("宜人性", 70),
            "宜人性较低": ("宜人性", 30),
            "神经质较高": ("神经质", 70),
            "神经质较低": ("神经质", 30),
        }
        
        for key, (dim, val) in level_map.items():
            if key in value:
                return (dim, val, None)
        
        return (None, None, None)

    def merge_all_features_comprehensively(self, features: List[Dict]) -> List[Dict]:
        """
        全面合并所有类型的特征
        
        策略：
        1. 解析复合特征（如 "外向性：65"）
        2. 按维度分组
        3. 计算综合权重（来源 × 时间 × 置信度）
        4. 加权合并数值型特征
        5. 保留非冲突的描述型特征
        """
        from collections import defaultdict
        
        dimension_features = defaultdict(list)
        type_features = defaultdict(list)
        
        for f in features:
            ftype = f.get("feature_type", "未知")
            value = f.get("feature_value", "")
            
            dim, num_val, level_val = self._parse_dimension_value(value)
            
            if dim:
                dimension_features[dim].append({
                    **f,
                    "_dimension": dim,
                    "_numeric_value": num_val or level_val,
                    "_weight": self._calculate_total_weight(f)
                })
            else:
                type_features[ftype].append({
                    **f,
                    "_weight": self._calculate_total_weight(f)
                })
        
        result = []
        
        numeric_dimensions = {"外向性", "开放性", "尽责性", "宜人性", "神经质"}
        
        for dim, dim_features in dimension_features.items():
            if dim in numeric_dimensions:
                numeric_vals = [(f["_numeric_value"], f["_weight"], f) 
                               for f in dim_features if f["_numeric_value"] is not None]
                
                if numeric_vals:
                    total_weight = sum(w for _, w, _ in numeric_vals)
                    if total_weight > 0:
                        weighted_avg = sum(v * w for v, w, _ in numeric_vals) / total_weight
                        best_feature = max(numeric_vals, key=lambda x: x[1])[2]
                        merged_feature = {k: v for k, v in best_feature.items() if not k.startswith("_")}
                        merged_feature["feature_value"] = str(int(round(weighted_avg)))
                        merged_feature["feature_type"] = dim
                        merged_feature["notes"] = f"合并自 {len(numeric_vals)} 个特征（加权平均）"
                        result.append(merged_feature)
                        print(f"合并维度特征 [{dim}]: {[(v, f.get('feature_value')) for v, w, f in numeric_vals]} -> {int(round(weighted_avg))}")
            else:
                sorted_features = sorted(dim_features, key=lambda x: x["_weight"], reverse=True)
                kept = [sorted_features[0]]
                for f in sorted_features[1:]:
                    is_conflict, _ = self.check_conflict_with_llm(kept[0], f)
                    if not is_conflict:
                        kept.append(f)
                for f in kept:
                    clean_f = {k: v for k, v in f.items() if not k.startswith("_")}
                    result.append(clean_f)
        
        for ftype, ftype_features in type_features.items():
            numeric_types = {"外向性", "开放性", "尽责性", "宜人性", "神经质"}
            
            if ftype in numeric_types:
                numeric_vals = []
                descriptive_vals = []
                
                for f in ftype_features:
                    num = self._extract_numeric_value(f.get("feature_value", ""))
                    level = self._get_level_value(f.get("feature_value", ""))
                    
                    if num is not None:
                        numeric_vals.append((num, f["_weight"], f))
                    elif level is not None:
                        numeric_vals.append((level, f["_weight"], f))
                    else:
                        descriptive_vals.append(f)
                
                if numeric_vals:
                    total_weight = sum(w for _, w, _ in numeric_vals)
                    if total_weight > 0:
                        weighted_avg = sum(v * w for v, w, _ in numeric_vals) / total_weight
                        best_feature = max(numeric_vals, key=lambda x: x[1])[2]
                        merged_feature = {k: v for k, v in best_feature.items() if not k.startswith("_")}
                        merged_feature["feature_value"] = str(int(round(weighted_avg)))
                        merged_feature["notes"] = f"合并自 {len(numeric_vals)} 个特征"
                        result.append(merged_feature)
                        print(f"合并数值特征 [{ftype}]: {[v for v, w, f in numeric_vals]} -> {int(round(weighted_avg))}")
                
                for f in descriptive_vals:
                    clean_f = {k: v for k, v in f.items() if not k.startswith("_")}
                    result.append(clean_f)
            else:
                sorted_features = sorted(ftype_features, key=lambda x: x["_weight"], reverse=True)
                kept = [sorted_features[0]]
                for f in sorted_features[1:]:
                    is_conflict, _ = self.check_conflict_with_llm(kept[0], f)
                    if not is_conflict:
                        kept.append(f)
                for f in kept:
                    clean_f = {k: v for k, v in f.items() if not k.startswith("_")}
                    result.append(clean_f)
        
        numeric_dimensions = {"外向性", "开放性", "尽责性", "宜人性", "神经质"}
        final_result = []
        seen_dimensions = {}
        
        for f in result:
            ftype = f.get("feature_type", "")
            if ftype in numeric_dimensions:
                if ftype not in seen_dimensions:
                    seen_dimensions[ftype] = f
                    final_result.append(f)
                else:
                    existing = seen_dimensions[ftype]
                    existing_weight = existing.get("confidence", 0.5)
                    new_weight = f.get("confidence", 0.5)
                    if new_weight > existing_weight:
                        final_result.remove(existing)
                        seen_dimensions[ftype] = f
                        final_result.append(f)
            else:
                final_result.append(f)
        
        return final_result


feature_merger = FeatureMerger()
