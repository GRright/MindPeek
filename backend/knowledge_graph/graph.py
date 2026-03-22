"""
知识图谱模块 - 用于特征关联推理
"""
import json
from datetime import datetime
from typing import Dict, List, Optional, Set, Tuple, Any
from dataclasses import dataclass, field
import networkx as nx
from collections import defaultdict


@dataclass
class KnowledgeNode:
    node_id: int
    node_type: str
    node_name: str
    properties: Dict[str, Any] = field(default_factory=dict)
    weight: float = 1.0


@dataclass
class KnowledgeEdge:
    source_id: int
    target_id: int
    relation_type: str
    weight: float = 1.0
    evidence: List[str] = field(default_factory=list)


class PersonalityKnowledgeBase:
    """人格心理学知识库"""
    
    MBTI_RELATIONS = {
        ("内向型", "社交回避"): ("implies", 0.85),
        ("内向型", "独处偏好"): ("implies", 0.9),
        ("外向型", "社交活跃"): ("implies", 0.85),
        ("外向型", "群体偏好"): ("implies", 0.8),
        ("直觉型", "抽象思维"): ("implies", 0.8),
        ("感觉型", "具体思维"): ("implies", 0.8),
        ("思考型", "理性决策"): ("implies", 0.85),
        ("情感型", "感性决策"): ("implies", 0.85),
        ("判断型", "计划性"): ("implies", 0.8),
        ("感知型", "灵活性"): ("implies", 0.8),
    }
    
    BIG_FIVE_TRAITS = {
        "开放性": ["好奇心", "创造力", "艺术兴趣", "求新求变"],
        "尽责性": ["自律", "目标导向", "可靠性", "勤奋"],
        "外向性": ["社交活跃", "乐观", "自信", "活力"],
        "宜人性": ["信任他人", "利他主义", "合作", "同理心"],
        "神经质": ["情绪波动", "焦虑倾向", "敏感", "压力反应"]
    }
    
    BEHAVIOR_PATTERNS = {
        "夜猫子": {"关联": ["创造力", "开放性"], "冲突": ["早睡早起"]},
        "早起型": {"关联": ["尽责性", "自律"], "冲突": ["熬夜"]},
        "线上社交偏好": {"关联": ["内向型", "社交回避"], "冲突": ["线下社交活跃"]},
        "线下社交活跃": {"关联": ["外向型", "社交活跃"], "冲突": ["社交回避"]},
        "冲动消费": {"关联": ["开放性", "求新求变"], "冲突": ["理性消费"]},
        "理性消费": {"关联": ["尽责性", "理性决策"], "冲突": ["冲动消费"]},
    }
    
    IMPLICIT_NEEDS = {
        "社交回避": {"潜在需求": ["安全感", "独处空间"], "可能问题": ["社交焦虑", "内向"]},
        "追求认可": {"潜在需求": ["自我价值", "归属感"], "可能问题": ["自尊问题"]},
        "完美主义": {"潜在需求": ["控制感", "成就感"], "可能问题": ["焦虑", "压力"]},
        "拖延行为": {"潜在需求": ["自主权"], "可能问题": ["执行力不足", "焦虑"]},
    }


class KnowledgeGraph:
    """知识图谱核心类"""
    
    def __init__(self):
        self.graph = nx.DiGraph()
        self.node_index: Dict[str, int] = {}
        self.node_counter = 0
        self.knowledge_base = PersonalityKnowledgeBase()
        self._init_base_knowledge()
    
    def _init_base_knowledge(self):
        """初始化基础知识图谱"""
        for (source, target), (relation, weight) in self.knowledge_base.MBTI_RELATIONS.items():
            self.add_relation(source, target, relation, weight)
        
        for trait, related_traits in self.knowledge_base.BIG_FIVE_TRAITS.items():
            for related in related_traits:
                self.add_relation(trait, related, "has_trait", 0.7)
        
        for behavior, relations in self.knowledge_base.BEHAVIOR_PATTERNS.items():
            for related in relations.get("关联", []):
                self.add_relation(behavior, related, "correlates_with", 0.7)
            for conflict in relations.get("冲突", []):
                self.add_relation(behavior, conflict, "conflicts_with", 0.8)
    
    def _get_or_create_node(self, node_name: str, node_type: str = "feature") -> int:
        key = f"{node_type}:{node_name}"
        if key not in self.node_index:
            self.node_counter += 1
            self.node_index[key] = self.node_counter
            self.graph.add_node(
                self.node_counter,
                name=node_name,
                type=node_type,
                weight=1.0,
                created_at=datetime.now().isoformat()
            )
        return self.node_index[key]
    
    def add_relation(self, source: str, target: str, relation_type: str, weight: float = 1.0,
                     evidence: str = None):
        """添加关系"""
        source_id = self._get_or_create_node(source)
        target_id = self._get_or_create_node(target)
        
        self.graph.add_edge(
            source_id, target_id,
            relation=relation_type,
            weight=weight,
            evidence=[evidence] if evidence else []
        )
    
    def add_user_feature(self, user_id: str, feature_type: str, feature_value: str, 
                         confidence: float, source_message: str = None):
        """添加用户特征到知识图谱"""
        user_node = self._get_or_create_node(f"user_{user_id}", "user")
        feature_node = self._get_or_create_node(feature_value, feature_type)
        
        self.graph.add_edge(
            user_node, feature_node,
            relation="has_feature",
            weight=confidence,
            evidence=[source_message] if source_message else [],
            created_at=datetime.now().isoformat()
        )
        
        self._infer_related_features(user_id, feature_value, confidence)
    
    def _infer_related_features(self, user_id: str, feature_value: str, confidence: float):
        """基于知识图谱推断相关特征"""
        user_node = self._get_or_create_node(f"user_{user_id}", "user")
        feature_node = self._get_or_create_node(feature_value)
        
        for neighbor in self.graph.successors(feature_node):
            edge_data = self.graph.get_edge_data(feature_node, neighbor)
            if edge_data and edge_data.get("relation") == "implies":
                inferred_confidence = confidence * edge_data.get("weight", 0.5)
                neighbor_name = self.graph.nodes[neighbor].get("name")
                neighbor_type = self.graph.nodes[neighbor].get("type")
                
                existing_edge = self.graph.get_edge_data(user_node, neighbor)
                if existing_edge:
                    if inferred_confidence > existing_edge.get("weight", 0):
                        self.graph[user_node][neighbor]["weight"] = inferred_confidence
                        self.graph[user_node][neighbor]["inferred"] = True
                else:
                    self.graph.add_edge(
                        user_node, neighbor,
                        relation="has_feature",
                        weight=inferred_confidence,
                        inferred=True,
                        source_feature=feature_value
                    )
    
    def get_user_features(self, user_id: str) -> List[Dict]:
        """获取用户所有特征"""
        user_node = self._get_or_create_node(f"user_{user_id}", "user")
        features = []
        
        for neighbor in self.graph.successors(user_node):
            edge_data = self.graph.get_edge_data(user_node, neighbor)
            node_data = self.graph.nodes[neighbor]
            
            features.append({
                "feature_type": node_data.get("type", "unknown"),
                "feature_value": node_data.get("name", ""),
                "confidence": edge_data.get("weight", 0),
                "inferred": edge_data.get("inferred", False),
                "evidence": edge_data.get("evidence", []),
                "source_feature": edge_data.get("source_feature")
            })
        
        return sorted(features, key=lambda x: x["confidence"], reverse=True)
    
    def find_conflicts(self, user_id: str) -> List[Dict]:
        """发现特征冲突"""
        user_node = self._get_or_create_node(f"user_{user_id}", "user")
        conflicts = []
        
        user_features = set()
        for neighbor in self.graph.successors(user_node):
            user_features.add(neighbor)
        
        for feature_a in user_features:
            for feature_b in user_features:
                if feature_a != feature_b:
                    if self.graph.has_edge(feature_a, feature_b):
                        edge_data = self.graph.get_edge_data(feature_a, feature_b)
                        if edge_data.get("relation") == "conflicts_with":
                            conflicts.append({
                                "feature_a": self.graph.nodes[feature_a].get("name"),
                                "feature_b": self.graph.nodes[feature_b].get("name"),
                                "conflict_weight": edge_data.get("weight", 0)
                            })
        
        return conflicts

    def add_social_relationship(self, user_id: str, person_name: str,
                               relationship_type: str, confidence: float = 0.8,
                               evidence: List[str] = None):
        """添加社会关系"""
        user_node = self._get_or_create_node(f"user_{user_id}", "user")
        person_node = self._get_or_create_node(f"person:{person_name}", "person")
        relation_node = self._get_or_create_node(f"relation:{relationship_type}", relationship_type)

        self.graph.add_edge(
            user_node, relation_node,
            relation="has_relationship",
            weight=confidence,
            person=person_name,
            evidence=evidence or [],
            created_at=datetime.now().isoformat()
        )

        self.graph.add_edge(
            relation_node, person_node,
            relation="to",
            weight=confidence,
            created_at=datetime.now().isoformat()
        )

    def get_user_relationships(self, user_id: str) -> List[Dict]:
        """获取用户的社会关系"""
        user_node = self._get_or_create_node(f"user_{user_id}", "user")
        relationships = []

        for neighbor in self.graph.successors(user_node):
            edge_data = self.graph.get_edge_data(user_node, neighbor)
            if edge_data and edge_data.get("relation") == "has_relationship":
                person = edge_data.get("person", "")
                relation_type = self.graph.nodes[neighbor].get("type", "")

                for second_neighbor in self.graph.successors(neighbor):
                    second_edge_data = self.graph.get_edge_data(neighbor, second_neighbor)
                    if second_edge_data and second_edge_data.get("relation") == "to":
                        relationships.append({
                            "person_name": self.graph.nodes[second_neighbor].get("name", ""),
                            "relationship_type": relation_type,
                            "confidence": edge_data.get("weight", 0),
                            "evidence": edge_data.get("evidence", [])
                        })

        return relationships

    def get_feature_correlations(self, feature_value: str, max_depth: int = 2) -> Dict:
        """获取特征相关性"""
        feature_node = self._get_or_create_node(feature_value)
        correlations = {
            "implies": [],
            "correlates_with": [],
            "conflicts_with": []
        }
        
        if feature_node not in self.graph:
            return correlations
        
        for neighbor in self.graph.successors(feature_node):
            edge_data = self.graph.get_edge_data(feature_node, neighbor)
            relation = edge_data.get("relation", "")
            neighbor_name = self.graph.nodes[neighbor].get("name")
            
            if relation in correlations:
                correlations[relation].append({
                    "feature": neighbor_name,
                    "weight": edge_data.get("weight", 0)
                })
        
        return correlations
    
    def export_graph(self) -> Dict:
        """导出图谱数据"""
        nodes = []
        edges = []
        
        for node_id, node_data in self.graph.nodes(data=True):
            nodes.append({
                "id": node_id,
                "label": node_data.get("name", ""),
                "type": node_data.get("type", ""),
                "weight": node_data.get("weight", 1.0)
            })
        
        for source, target, edge_data in self.graph.edges(data=True):
            edges.append({
                "source": source,
                "target": target,
                "relation": edge_data.get("relation", ""),
                "weight": edge_data.get("weight", 1.0),
                "inferred": edge_data.get("inferred", False)
            })
        
        return {"nodes": nodes, "edges": edges}
    
    def get_user_subgraph(self, user_id: str) -> Dict:
        """获取用户相关的子图"""
        user_node = self._get_or_create_node(f"user_{user_id}", "user")
        
        user_nodes = {user_node}
        user_edges = []
        
        for neighbor in self.graph.successors(user_node):
            user_nodes.add(neighbor)
            edge_data = self.graph.get_edge_data(user_node, neighbor)
            user_edges.append({
                "source": user_node,
                "target": neighbor,
                "relation": edge_data.get("relation", ""),
                "weight": edge_data.get("weight", 1.0)
            })
            
            for second_neighbor in self.graph.successors(neighbor):
                user_nodes.add(second_neighbor)
                edge_data2 = self.graph.get_edge_data(neighbor, second_neighbor)
                user_edges.append({
                    "source": neighbor,
                    "target": second_neighbor,
                    "relation": edge_data2.get("relation", ""),
                    "weight": edge_data2.get("weight", 1.0)
                })
        
        nodes = []
        for node_id in user_nodes:
            node_data = self.graph.nodes[node_id]
            nodes.append({
                "id": node_id,
                "label": node_data.get("name", ""),
                "type": node_data.get("type", "")
            })
        
        return {"nodes": nodes, "edges": user_edges}


knowledge_graph = KnowledgeGraph()
