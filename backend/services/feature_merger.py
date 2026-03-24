"""
特征智能合并服务 - 用于识别和合并相似特征
"""
import re
from typing import List, Dict, Tuple, Optional
from difflib import SequenceMatcher


class FeatureMerger:
    """特征智能合并器"""

    def __init__(self):
        self.synonyms = self._load_synonyms()
        self.abbreviations = self._load_abbreviations()

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
        在现有特征中找到最佳匹配
        
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


feature_merger = FeatureMerger()
