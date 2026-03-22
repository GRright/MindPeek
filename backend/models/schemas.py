"""
Pydantic数据模型定义
"""
from datetime import datetime
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field
from enum import Enum


class FeatureTypeEnum(str, Enum):
    MBTI = "MBTI"
    BIG_FIVE = "大五人格"
    BEHAVIOR_HABIT = "行为习惯"
    POTENTIAL_THOUGHT = "潜在想法"
    INTEREST = "兴趣爱好"
    VALUE = "价值观"


class MessageRole(str, Enum):
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class FeatureBase(BaseModel):
    feature_type: str
    feature_value: str
    confidence: float = Field(ge=0.0, le=1.0)
    source_message: Optional[str] = None
    reasoning: Optional[str] = None
    evidence: List[str] = []


class FeatureCreate(FeatureBase):
    pass


class FeatureResponse(FeatureBase):
    id: int
    user_id: str
    created_at: datetime
    updated_at: datetime
    is_active: bool = True
    
    class Config:
        from_attributes = True


class MessageBase(BaseModel):
    role: MessageRole
    content: str


class MessageCreate(MessageBase):
    session_id: Optional[str] = None


class MessageResponse(MessageBase):
    id: int
    user_id: str
    timestamp: datetime
    session_id: Optional[str] = None
    
    class Config:
        from_attributes = True


class ProfileBase(BaseModel):
    user_id: str
    profile_data: Dict[str, Any] = {}
    summary: Optional[str] = None


class ProfileResponse(ProfileBase):
    id: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class ProfileSummary(BaseModel):
    user_id: str
    mbti: Optional[str] = None
    big_five: Dict[str, float] = {}
    behavior_habits: List[str] = []
    potential_thoughts: List[str] = []
    interests: List[str] = []
    values: List[str] = []
    confidence_score: float = 0.0
    total_features: int = 0
    conversation_count: int = 0


class ChatRequest(BaseModel):
    user_id: str
    message: str
    session_id: Optional[str] = None
    extract_features: bool = True
    deep_think: bool = False


class ChatResponse(BaseModel):
    response: str
    features_extracted: List[FeatureBase] = []
    profile_updated: bool = False
    session_id: Optional[str] = None
    think_content: Optional[str] = None


class LLMConfigRequest(BaseModel):
    provider: str
    api_key: str
    model: Optional[str] = None
    api_url: Optional[str] = None


class LLMConfigResponse(BaseModel):
    provider: str
    enabled: bool
    model: str
    configured: bool


class KnowledgeNode(BaseModel):
    id: int
    node_type: str
    node_name: str
    properties: Dict[str, Any] = {}


class KnowledgeEdge(BaseModel):
    source_id: int
    target_id: int
    relation_type: str
    weight: float = 1.0


class KnowledgeGraphResponse(BaseModel):
    nodes: List[KnowledgeNode]
    edges: List[KnowledgeEdge]


class AgentTaskRequest(BaseModel):
    task_type: str
    input_data: Dict[str, Any]


class AgentTaskResponse(BaseModel):
    task_id: int
    status: str
    output_data: Dict[str, Any] = {}


class UserProfileDetail(BaseModel):
    user_id: str
    username: Optional[str] = None
    profile: Optional[ProfileResponse] = None
    features: List[FeatureResponse] = []
    recent_conversations: List[MessageResponse] = []
    knowledge_graph: Optional[KnowledgeGraphResponse] = None
    summary: Optional[ProfileSummary] = None
    metadata: Optional[Dict[str, Any]] = None


class FeatureExtractionRequest(BaseModel):
    user_id: str
    messages: List[MessageBase]
    existing_features: List[FeatureBase] = []


class FeatureExtractionResponse(BaseModel):
    features: List[FeatureBase]
    correlation_analysis: str = ""
    new_insights: str = ""
    confidence_updates: Dict[str, float] = {}
