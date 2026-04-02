"""
Agent 协作流程图 - 对话时的 Agent 触发流程
"""
from diagrams import Diagram, Cluster, Edge
from diagrams.programming.framework import FastAPI
from diagrams.programming.language import Python
from diagrams.generic.device import Device
from diagrams.generic.storage import Storage
from diagrams.onprem.database import Database
from diagrams.custom import Custom

graph_attr = {
    "fontsize": "45",
    "bgcolor": "white",
    "label": "Agent 协作流程 - 对话触发",
    "fontname": "Microsoft YaHei",
    "rankdir": "TB",
}

with Diagram("Agent 协作流程", show=False, direction="TB", graph_attr=graph_attr):
    # 用户发送消息
    user = Device("用户发送消息")
    
    # 第一步：意图识别
    with Cluster("1. 意图识别"):
        intent_classifier = Custom("IntentClassifier\n语义 Embedding 判断", "icons/intent.png")
        personal_keywords = Storage("personal_keywords\n个人化关键词")
        general_keywords = Storage("general_keywords\n通用问题关键词")
    
    # 第二步：加载上下文
    with Cluster("2. 加载用户上下文"):
        profile_service = Custom("ProfileService\n读取用户画像", "icons/profile.png")
        sqlite = Storage("SQLite\n特征数据库")
        
        with Cluster("画像数据"):
            mbti = Custom("MBTI 特征", "icons/mbti.png")
            bigfive = Custom("大五人格", "icons/bigfive.png")
            behavior = Custom("行为习惯", "icons/behavior.png")
            interests = Custom("兴趣爱好", "icons/interest.png")
            values = Custom("价值观", "icons/value.png")
    
    # 第三步：生成回复
    with Cluster("3. 生成 AI 回复"):
        llm = Custom("LLM\n(Qwen/OpenAI)", "icons/llm.png")
        chat_graph = Custom("LangGraph\nChatGraph", "icons/graph.png")
        personalized_prompt = Custom("个性化提示词\n融入用户画像", "icons/prompt.png")
    
    # 第四步：特征提取
    with Cluster("4. 特征提取 (异步)"):
        feature_discovery = Custom("FeatureDiscoveryAgent\n自主特征发现", "icons/discovery.png")
        personal_info = Custom("PersonalInfoAgent\n个人信息提取", "icons/personal.png")
        llm_extract = Custom("LLM\n特征分析", "icons/llm.png")
    
    # 第五步：关联分析与更新
    with Cluster("5. 关联分析与画像更新"):
        correlation_agent = Custom("CorrelationAgent\n特征关联分析", "icons/correlation.png")
        knowledge_graph = Custom("KnowledgeGraph\n关联推断", "icons/graph.png")
        profile_update = Custom("ProfileService\n更新画像", "icons/profile.png")
    
    # 第六步：异步后台任务
    with Cluster("6. 异步后台任务"):
        async_orchestrator = Custom("AsyncAgentOrchestrator\n任务调度", "icons/orchestrator.png")
        
        deep_think = Custom("深度思考分析", "icons/think.png")
        latent_intent = Custom("潜在意图发现", "icons/latent.png")
        stability = Custom("特征稳定性评估", "icons/stability.png")
    
    # 流程连接
    user >> intent_classifier
    personal_keywords >> intent_classifier
    general_keywords >> intent_classifier
    
    intent_classifier >> Edge(label="需要个性化") >> profile_service
    intent_classifier >> Edge(label="通用问题") >> llm
    
    profile_service >> sqlite
    sqlite >> mbti
    sqlite >> bigfive
    sqlite >> behavior
    sqlite >> interests
    sqlite >> values
    
    mbti >> personalized_prompt
    bigfive >> personalized_prompt
    behavior >> personalized_prompt
    interests >> personalized_prompt
    values >> personalized_prompt
    
    personalized_prompt >> chat_graph
    chat_graph >> llm
    
    # 特征提取流程
    chat_graph >> Edge(label="对话同时") >> feature_discovery
    chat_graph >> Edge(label="对话同时") >> personal_info
    
    feature_discovery >> llm_extract
    personal_info >> llm_extract
    
    # 关联分析
    feature_discovery >> correlation_agent
    personal_info >> correlation_agent
    correlation_agent >> knowledge_graph
    knowledge_graph >> profile_update
    profile_update >> sqlite
    
    # 异步任务
    profile_update >> async_orchestrator
    async_orchestrator >> deep_think
    async_orchestrator >> latent_intent
    async_orchestrator >> stability
    
    deep_think >> llm
    latent_intent >> llm
    stability >> llm
