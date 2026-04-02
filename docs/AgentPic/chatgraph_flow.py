"""
LangGraph ChatGraph 状态图
"""
from diagrams import Diagram, Cluster, Edge
from diagrams.programming.framework import FastAPI
from diagrams.programming.language import Python
from diagrams.generic.storage import Storage
from diagrams.custom import Custom

graph_attr = {
    "fontsize": "45",
    "bgcolor": "white",
    "label": "LangGraph ChatGraph 状态流转",
    "fontname": "Microsoft YaHei",
}

with Diagram("ChatGraph 状态图", show=False, direction="TB", graph_attr=graph_attr):
    
    # 入口
    start = Custom("用户输入\n(user_id, message)", "icons/start.png")
    
    # 节点 1: 保存用户消息
    save_user = Custom("Node: save_user_message\n\n保存用户消息到数据库", "icons/save.png")
    
    # 节点 2: 加载上下文
    load_context = Custom("Node: load_context\n\n加载用户画像数据:\n- 基本信息\n- MBTI/大五人格\n- 行为习惯/兴趣爱好\n- 价值观/情感状态\n- 社会关系/推断特征", "icons/load.png")
    
    # 节点 3: 加载对话历史
    load_history = Custom("Node: load_conversation_history\n\n加载最近 6 轮对话", "icons/history.png")
    
    # 条件分支：意图识别
    with Cluster("路由决策"):
        route_decision = Custom("_should_use_personalization\n\n混合判断方法:\n1. emotional_keywords 情绪关键词\n2. personal_keywords 个人关键词\n3. general_keywords 通用关键词\n4. IntentClassifier Embedding", "icons/route.png")
        
        personalized_branch = Custom("use_personalization\n分支", "icons/personalized.png")
        general_branch = Custom("general\n分支", "icons/general.png")
    
    # 节点 4a: 生成个性化回复
    generate_personalized = Custom("Node: generate_personalized_response\n\n构建个性化提示词:\n- 自然融入用户特征\n- 情感共鸣\n- 预判需求\n- 保持自然\n- 尊重隐私", "icons/personalized.png")
    
    # 节点 4b: 生成通用回复
    generate_general = Custom("Node: generate_general_response\n\n通用回答模式:\n- 直接回答问题\n- 简洁清晰\n- 无需个性化", "icons/general.png")
    
    # 节点 5: 特征提取
    extract_features = Custom("Node: extract_features\n\n双 Agent 特征提取:\n\n1. FeatureDiscoveryAgent\n   - 14 种特征类型\n   - 置信度评估\n   - 去重\n\n2. PersonalInfoAgent\n   - 个人信息\n   - 关系网络\n   - 并行提取", "icons/extract.png")
    
    # 节点 6: 更新画像
    update_profile = Custom("Node: update_profile\n\n1. 保存特征到数据库\n2. CorrelationAgent 关联分析\n3. 推断新特征\n4. 提交异步任务", "icons/update.png")
    
    # 条件分支：深度思考
    with Cluster("深度思考决策"):
        deep_think_decision = Custom("should_deep_think\n\n判断是否进行深度思考", "icons/decision.png")
        deep_think_branch = Custom("deep_think\n分支", "icons/think.png")
        skip_branch = Custom("skip_deep_think\n分支", "icons/skip.png")
    
    # 节点 7: 深度思考分析
    deep_think_node = Custom("Node: deep_think_analysis\n\n提交异步任务:\n- TaskType.DEEP_THINK\n- 结合用户画像\n- 心理状态分析", "icons/think.png")
    
    # 节点 8: 保存助手回复
    save_assistant = Custom("Node: save_assistant_message\n\n保存 AI 回复到数据库", "icons/save.png")
    
    # 结束
    end = Custom("END\n返回 response\nextracted_features\nthink_content", "icons/end.png")
    
    # 数据存储
    sqlite = Storage("SQLite\n数据库")
    
    # 流程连接
    start >> save_user
    save_user >> load_context
    load_context >> load_history
    load_history >> route_decision
    
    route_decision >> personalized_branch
    route_decision >> general_branch
    
    personalized_branch >> generate_personalized
    general_branch >> generate_general
    
    generate_personalized >> extract_features
    generate_general >> extract_features
    
    extract_features >> update_profile
    update_profile >> sqlite
    
    update_profile >> deep_think_decision
    
    deep_think_decision >> deep_think_branch
    deep_think_decision >> skip_branch
    
    deep_think_branch >> deep_think_node
    skip_branch >> save_assistant
    
    deep_think_node >> save_assistant
    save_assistant >> end
    save_assistant >> sqlite
