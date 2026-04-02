"""
Agent 系统架构图 - 使用 Diagrams 库绘制
"""
from diagrams import Diagram, Cluster, Edge
from diagrams.programming.framework import FastAPI, Vue
from diagrams.programming.language import Python, JavaScript
from diagrams.generic.device import Device
from diagrams.generic.storage import Storage
from diagrams.ml import TensorFlow
from diagrams.onprem.database import PostgreSQL
from diagrams.onprem.compute import Server
from diagrams.custom import Custom

# 设置图形属性
graph_attr = {
    "fontsize": "45",
    "bgcolor": "white",
    "label": "MindPeek Agent 系统架构",
    "fontname": "Microsoft YaHei",
}

with Diagram("Agent 系统架构", show=False, direction="TB", graph_attr=graph_attr):
    # 用户界面层
    user = Device("用户")
    frontend = Vue("前端界面\n(ChatView)")
    
    # API 层
    with Cluster("API 层"):
        api_server = FastAPI("FastAPI\nAPI Server")
        chat_graph = Custom("LangGraph\nChatGraph", "icons/graph.png")
    
    # Agent 核心层
    with Cluster("Agent 核心层"):
        with Cluster("同步分析 Agents"):
            mbti_agent = Python("MBTIAgent\n性格分析")
            bigfive_agent = Python("BigFiveAgent\n大五人格")
            behavior_agent = Python("BehaviorHabitAgent\n行为习惯")
            implicit_intent_agent = Python("ImplicitIntentAgent\n隐性意图")
            correlation_agent = Python("CorrelationAgent\n特征关联")
        
        with Cluster("异步任务编排"):
            async_orchestrator = Custom("AsyncAgentOrchestrator\n任务调度", "icons/orchestrator.png")
            
            with Cluster("后台异步任务"):
                deep_think = Custom("深度思考分析", "icons/think.png")
                feature_corr = Custom("特征关联分析", "icons/correlation.png")
                relationship = Custom("社会关系发现", "icons/relationship.png")
                memory = Custom("记忆整合", "icons/memory.png")
                latent_intent = Custom("潜在意图发现", "icons/latent.png")
                stability = Custom("稳定性评估", "icons/stability.png")
        
        with Cluster("特征发现 Agents"):
            feature_discovery = Custom("FeatureDiscoveryAgent\n特征发现", "icons/discovery.png")
            personal_info = Custom("PersonalInfoAgent\n个人信息", "icons/personal.png")
            intent_classifier = Custom("IntentClassifier\n意图识别", "icons/intent.png")
    
    # 服务层
    with Cluster("服务层"):
        llm_provider = Custom("LLM Provider\n(Qwen/OpenAI)", "icons/llm.png")
        profile_service = Custom("ProfileService\n用户画像服务", "icons/profile.png")
        knowledge_graph = Custom("KnowledgeGraph\n知识图谱", "icons/graph.png")
    
    # 数据存储层
    with Cluster("数据存储层"):
        sqlite = Storage("SQLite\n(用户数据/特征/对话)")
        embedding_model = TensorFlow("SentenceTransformer\n意图识别模型")
    
    # 连接关系
    user >> frontend
    frontend >> api_server
    api_server >> chat_graph
    chat_graph >> intent_classifier
    chat_graph >> feature_discovery
    chat_graph >> personal_info
    
    intent_classifier >> llm_provider
    feature_discovery >> llm_provider
    personal_info >> llm_provider
    
    mbti_agent >> llm_provider
    bigfive_agent >> llm_provider
    behavior_agent >> llm_provider
    implicit_intent_agent >> llm_provider
    
    feature_discovery >> correlation_agent
    correlation_agent >> knowledge_graph
    
    chat_graph >> async_orchestrator
    async_orchestrator >> deep_think
    async_orchestrator >> feature_corr
    async_orchestrator >> relationship
    async_orchestrator >> memory
    async_orchestrator >> latent_intent
    async_orchestrator >> stability
    
    deep_think >> llm_provider
    feature_corr >> llm_provider
    relationship >> llm_provider
    memory >> llm_provider
    latent_intent >> llm_provider
    stability >> llm_provider
    
    mbti_agent >> sqlite
    bigfive_agent >> sqlite
    behavior_agent >> sqlite
    feature_discovery >> sqlite
    personal_info >> sqlite
    
    intent_classifier >> embedding_model
    profile_service >> sqlite
    knowledge_graph >> sqlite
