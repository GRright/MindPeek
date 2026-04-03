"""
Agent 分类与功能图
"""
from diagrams import Diagram, Cluster, Edge
from diagrams.programming.language import Python
from diagrams.custom import Custom

graph_attr = {
    "fontsize": "45",
    "bgcolor": "white",
    "label": "Agent 分类与功能详解",
    "fontname": "Microsoft YaHei",
}

with Diagram("Agent 分类", show=False, direction="TB", graph_attr=graph_attr):
    
    # 第一层：Agent 编排器
    orchestrator = Custom("AgentOrchestrator\nAgent 编排器", "icons/orchestrator.png")
    
    # 第二层：同步分析 Agents
    with Cluster("同步分析 Agents (实时调用 LLM)"):
        with Cluster("人格分析 Agents"):
            mbti = Python("MBTIAgent\n\nMBTI 四个维度分析:\n- E/I 外向/内向\n- S/N 感觉/直觉\n- T/F 思考/情感\n- J/P 判断/知觉")
            bigfive = Python("BigFiveAgent\n\n大五人格分析:\n- 开放性\n- 尽责性\n- 外向性\n- 宜人性\n- 神经质")
        
        with Cluster("行为与意图 Agents"):
            behavior = Python("BehaviorHabitAgent\n\n行为习惯分析:\n- 作息习惯\n- 消费习惯\n- 社交习惯\n- 沟通风格\n- 学习/工作习惯")
            
            implicit_intent = Python("ImplicitIntentAgent\n\n隐性意图分析:\n- 未明说的需求\n- 潜在顾虑\n- 隐藏偏好\n- 情感状态")
        
        with Cluster("特征处理 Agents"):
            correlation = Python("CorrelationAgent\n\n特征关联分析:\n- 发现特征关联\n- 推断新特征\n- 检测冲突")
    
    # 第三层：独立 Agents
    with Cluster("独立功能 Agents"):
        feature_discovery = Custom("FeatureDiscoveryAgent\n\n基于 LangGraph 的自主特征发现:\n1. 分析消息发现特征\n2. 验证与去重\n3. 决定存储策略\n4. 生成洞察报告\n\n预定义 14 种特征类型", "icons/discovery.png")
        
        personal_info = Custom("PersonalInfoAgent\n\n个人信息与关系提取:\n- 基本信息：姓名/年龄/职业/居住地\n- 教育背景/婚姻状况\n- 关系网络发现\n- 并行提取", "icons/personal.png")
        
        intent_classifier = Custom("IntentClassifier\n\n基于语义 Embedding 的意图识别:\n- 20 个个性化模板\n- 20 个通用模板\n- SentenceTransformer 模型\n- 余弦相似度判断", "icons/intent.png")
        
        prediction = Custom("PredictionAgent\n\n用户行为预测:\n- 行为预测\n- 想法预测\n- 情感预测\n- 决策预测\n\n时间范围：短期/中期/长期", "icons/predict.png")
    
    # 第四层：异步任务编排
    with Cluster("AsyncAgentOrchestrator (异步任务编排器)"):
        async_orchestrator = Custom("任务调度与并发控制\n最大并发数：3", "icons/orchestrator.png")
        
        with Cluster("6 种异步任务类型"):
            deep_think = Custom("DEEP_THINK\n深度思考分析\n- 心理状态分析\n- 潜在需求识别\n- 人格洞察", "icons/think.png")
            
            feature_corr = Custom("FEATURE_CORRELATION\n特征关联分析\n- 关联发现\n- 特征推断", "icons/correlation.png")
            
            relationship = Custom("RELATIONSHIP_DISCOVERY\n社会关系发现\n- 人物关系识别\n- 互动模式分析", "icons/relationship.png")
            
            memory = Custom("MEMORY_CONSOLIDATION\n记忆整合\n- 短期→长期记忆\n- 信息整合", "icons/memory.png")
            
            latent_intent = Custom("LATENT_INTENT\n潜在意图发现\n- 隐性需求挖掘\n- 行为预测", "icons/latent.png")
            
            stability = Custom("STABILITY_EVALUATION\n稳定性评估\n- 特征稳定性判断\n- 衰减率计算", "icons/stability.png")
    
    # 连接关系
    orchestrator >> mbti
    orchestrator >> bigfive
    orchestrator >> behavior
    orchestrator >> implicit_intent
    orchestrator >> correlation
    
    orchestrator >> Edge(label="协调调用") >> feature_discovery
    orchestrator >> Edge(label="协调调用") >> personal_info
    orchestrator >> Edge(label="协调调用") >> intent_classifier
    
    feature_discovery >> async_orchestrator
    personal_info >> async_orchestrator
    correlation >> async_orchestrator
    
    async_orchestrator >> deep_think
    async_orchestrator >> feature_corr
    async_orchestrator >> relationship
    async_orchestrator >> memory
    async_orchestrator >> latent_intent
    async_orchestrator >> stability
