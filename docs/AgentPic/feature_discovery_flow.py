"""
FeatureDiscovery Agent 工作流程图
"""
from diagrams import Diagram, Cluster, Edge
from diagrams.programming.language import Python
from diagrams.generic.storage import Storage
from diagrams.custom import Custom

graph_attr = {
    "fontsize": "45",
    "bgcolor": "white",
    "label": "FeatureDiscovery Agent 工作流程",
    "fontname": "Microsoft YaHei",
}

with Diagram("FeatureDiscovery 流程", show=False, direction="TB", graph_attr=graph_attr):
    
    # 输入
    user_message = Custom("用户消息\n+ 对话历史", "icons/message.png")
    existing_features = Storage("已有特征\n(最多 15 条)")
    
    # 第一步：分析消息
    with Cluster("Step 1: analyze_message"):
        analysis_prompt = Custom("构建分析提示词\n\n- 14 种预定义特征类型\n- 置信度评估 (0-1)\n- 证据提取", "icons/prompt.png")
        llm_analysis = Custom("LLM 分析\n提取特征", "icons/llm.png")
        json_parse = Custom("JSON 解析\n提取 discovered_features", "icons/parse.png")
    
    # 第二步：验证特征
    with Cluster("Step 2: validate_features"):
        confidence_filter = Custom("置信度过滤\n< 50% 丢弃", "icons/filter.png")
        duplicate_check = Custom("重复检查\n\n- 与已有特征对比\n- 高置信度更新低置信度\n- 避免重复记录", "icons/check.png")
        new_category = Custom("新类型发现\n\n\"新类型:建议名称\"\n→ 提取新分类", "icons/new.png")
    
    # 第三步：决定存储策略
    with Cluster("Step 3: decide_storage"):
        high_priority = Custom("高优先级 (≥80%)\n\n- 直接存储\n- 无需聚合\n- MBTI/大五人格默认高优", "icons/high.png")
        medium_priority = Custom("中优先级 (60-80%)\n\n- 需要聚合\n- 更多证据支持", "icons/medium.png")
        low_priority = Custom("低优先级 (<60%)\n\n- 需要聚合\n- 仅供参考", "icons/low.png")
    
    # 第四步：生成洞察
    with Cluster("Step 4: generate_insight"):
        insight_report = Custom("生成洞察报告\n\n- 新特征数量\n- 特征类型分布\n- 置信度统计", "icons/report.png")
    
    # 输出
    output_features = Storage("输出特征\n(discovered_features)")
    save_to_db = Custom("保存到数据库\nSQLite", "icons/database.png")
    
    # 流程连接
    user_message >> analysis_prompt
    existing_features >> analysis_prompt
    
    analysis_prompt >> llm_analysis
    llm_analysis >> json_parse
    
    json_parse >> confidence_filter
    confidence_filter >> duplicate_check
    duplicate_check >> new_category
    
    new_category >> high_priority
    new_category >> medium_priority
    new_category >> low_priority
    
    high_priority >> insight_report
    medium_priority >> insight_report
    low_priority >> insight_report
    
    insight_report >> output_features
    output_features >> save_to_db
