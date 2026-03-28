"""
意图分类器 - 基于语义 Embedding 的智能意图判断
"""
import numpy as np
from typing import List, Tuple
from sentence_transformers import SentenceTransformer


class IntentClassifier:
    """
    基于语义 embedding 的意图分类器
    使用余弦相似度判断用户消息是否需要个性化
    """

    PERSONAL_TEMPLATES = [
        "我最近感觉很焦虑",
        "我的性格是怎样的",
        "我应该如何选择",
        "我喜欢看科幻电影",
        "我最近工作压力很大",
        "我的兴趣爱好是什么",
        "我适合做什么工作",
        "我感到孤独怎么办",
        "你能推荐我一些书吗",
        "我最近总是失眠",
        "我的MBTI是什么",
        "我是个内向的人",
        "我应该如何和人相处",
        "我最近心情不好",
        "我的价值观是什么",
        "你能建议我该怎么学习吗",
        "我对自己很不自信",
        "我应该继续考研还是工作",
        "我喜欢的类型是",
        "我是一个完美主义者",
    ]

    GENERAL_TEMPLATES = [
        "什么是人工智能",
        "如何学习Python",
        "为什么天空是蓝色的",
        "介绍一下北京",
        "今天天气怎么样",
        "帮我写一段代码",
        "计算1+1等于多少",
        "解释一下相对论",
        "水的沸点是多少",
        "秦始皇是谁",
        "如何制作蛋糕",
        "地球到月亮的距离",
        "请翻译成英文",
        "计算机的基本组成",
        "光的传播速度",
        "什么是光合作用",
        "水的化学式是什么",
        "勾股定理是什么",
        "请帮我搜索一下",
        "这个单词怎么拼写",
    ]

    def __init__(self, model_name: str = "paraphrase-multilingual-MiniLM-L12-v2"):
        """
        初始化意图分类器

        Args:
            model_name: 使用的模型名称，默认使用多语言轻量级模型
        """
        self.model = SentenceTransformer(model_name)
        self._personal_embeddings: np.ndarray = None
        self._general_embeddings: np.ndarray = None
        self._initialize_embeddings()

    def _initialize_embeddings(self):
        """预计算意图模板的 embedding"""
        print(f">>> 初始化意图分类器，加载模型: {self.model_name}")
        self._personal_embeddings = self.model.encode(self.PERSONAL_TEMPLATES, convert_to_numpy=True)
        self._general_embeddings = self.model.encode(self.GENERAL_TEMPLATES, convert_to_numpy=True)
        print(f">>> 意图分类器初始化完成，共加载 {len(self.PERSONAL_TEMPLATES)} 个个性化模板，{len(self.GENERAL_TEMPLATES)} 个通用模板")

    def _cosine_similarity(self, vec1: np.ndarray, vec2: np.ndarray) -> float:
        """计算余弦相似度"""
        dot_product = np.dot(vec1, vec2)
        norm1 = np.linalg.norm(vec1)
        norm2 = np.linalg.norm(vec2)
        if norm1 == 0 or norm2 == 0:
            return 0.0
        return float(dot_product / (norm1 * norm2))

    def _compute_avg_similarity(self, query_embedding: np.ndarray, template_embeddings: np.ndarray) -> float:
        """计算查询与模板集合的平均相似度"""
        similarities = [self._cosine_similarity(query_embedding, te) for te in template_embeddings]
        return float(np.mean(similarities))

    def classify(self, message: str) -> Tuple[str, float]:
        """
        判断消息是否需要个性化

        Args:
            message: 用户消息

        Returns:
            (意图类型, 置信度)
            意图类型: "use_personalization" 或 "general"
            置信度: 0-1 之间，越高表示判断越确定
        """
        message_embedding = self.model.encode([message], convert_to_numpy=True)[0]

        personal_sim = self._compute_avg_similarity(message_embedding, self._personal_embeddings)
        general_sim = self._compute_avg_similarity(message_embedding, self._general_embeddings)

        similarity_diff = personal_sim - general_sim

        if similarity_diff > 0.02:
            confidence = min(0.95, 0.5 + similarity_diff)
            return "use_personalization", confidence
        elif similarity_diff < -0.02:
            confidence = min(0.95, 0.5 + abs(similarity_diff))
            return "general", confidence
        else:
            if personal_sim > 0.4:
                return "use_personalization", personal_sim
            else:
                return "general", 1.0 - personal_sim

    def should_use_personalization(self, message: str) -> bool:
        """
        快速判断方法

        Args:
            message: 用户消息

        Returns:
            True 表示应该使用个性化，False 表示通用回答
        """
        intent, confidence = self.classify(message)
        return intent == "use_personalization"


_intent_classifier: IntentClassifier = None


def get_intent_classifier() -> IntentClassifier:
    """获取全局意图分类器实例（单例）"""
    global _intent_classifier
    if _intent_classifier is None:
        _intent_classifier = IntentClassifier()
    return _intent_classifier
