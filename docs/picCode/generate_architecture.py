from diagrams import Diagram, Cluster, Edge
from diagrams.onprem.database import PostgreSQL, SQLite
from diagrams.programming.language import Vue
from diagrams.aws.compute import Lambda
from diagrams.generic.storage import Storage
from diagrams.onprem.compute import Server


def create_architecture_diagram(filename, title, lang):
    graph_attr = {
        "fontsize": "14",
        "bgcolor": "white",
        "splines": "ortho",
        "nodesep": "0.6",
        "ranksep": "1.2",
        "fontname": "Microsoft YaHei,SimHei,Arial",
    }
    
    node_attr = {
        "fontsize": "10",
        "fontname": "Microsoft YaHei,SimHei,Arial",
    }
    
    cluster_attr = {
        "fontsize": "12",
        "style": "filled",
        "fillcolor": "#f5f5f5",
        "fontname": "Microsoft YaHei,SimHei,Arial",
    }

    with Diagram(
        title,
        show=False,
        direction="TB",
        filename=f"docs/{filename}",
        graph_attr=graph_attr,
        node_attr=node_attr,
        outformat="png",
    ):
        with Cluster(lang["frontend"], graph_attr=cluster_attr):
            chat = Vue(lang["chat"])
            profile = Vue(lang["profile"])
            kg = Vue(lang["kg"])
            features = Vue(lang["features"])

        with Cluster(lang["agents"], graph_attr=cluster_attr):
            feature_agent = Lambda(lang["feature_agent"])
            intent_agent = Lambda(lang["intent_agent"])
            mbti_agent = Lambda(lang["mbti_agent"])
            prediction_agent = Lambda(lang["prediction_agent"])

        with Cluster(lang["services"], graph_attr=cluster_attr):
            profile_service = Server(lang["profile_service"])
            kg_service = Server(lang["kg_service"])
            llm_service = Server(lang["llm_service"])

        with Cluster(lang["storage"], graph_attr=cluster_attr):
            sqlite = SQLite(lang["sqlite"])
            memobase = Storage(lang["memobase"])
            llm = Server(lang["llm"])

        (chat, profile, kg, features) >> Edge(color="#333", style="solid", penwidth="2") >> (feature_agent, intent_agent, mbti_agent, prediction_agent)
        (feature_agent, intent_agent, mbti_agent, prediction_agent) >> Edge(color="#333", style="solid", penwidth="2") >> (profile_service, kg_service, llm_service)
        (profile_service, kg_service, llm_service) >> Edge(color="#333", style="solid", penwidth="2") >> (sqlite, memobase, llm)


lang_zh = {
    "frontend": "前端层",
    "chat": "聊天",
    "profile": "用户画像",
    "kg": "知识图谱",
    "features": "特征管理",
    "agents": "智能体层",
    "feature_agent": "特征发现",
    "intent_agent": "意图识别",
    "mbti_agent": "MBTI分析",
    "prediction_agent": "行为预测",
    "services": "服务层",
    "profile_service": "画像服务",
    "kg_service": "图谱服务",
    "llm_service": "LLM服务",
    "storage": "数据层",
    "sqlite": "SQLite",
    "memobase": "MemoBase",
    "llm": "LLM",
}

lang_en = {
    "frontend": "Frontend Layer",
    "chat": "Chat",
    "profile": "User Profile",
    "kg": "Knowledge Graph",
    "features": "Features",
    "agents": "Agents Layer",
    "feature_agent": "Feature Discovery",
    "intent_agent": "Intent Classification",
    "mbti_agent": "MBTI Analysis",
    "prediction_agent": "Prediction",
    "services": "Services Layer",
    "profile_service": "Profile Service",
    "kg_service": "Graph Service",
    "llm_service": "LLM Service",
    "storage": "Data Layer",
    "sqlite": "SQLite",
    "memobase": "MemoBase",
    "llm": "LLM",
}

lang_ja = {
    "frontend": "フロントエンド層",
    "chat": "チャット",
    "profile": "ユーザープロファイル",
    "kg": "ナレッジグラフ",
    "features": "特徴管理",
    "agents": "エージェント層",
    "feature_agent": "特徴発見",
    "intent_agent": "意図分類",
    "mbti_agent": "MBTI分析",
    "prediction_agent": "予測",
    "services": "サービス層",
    "profile_service": "プロファイルサービス",
    "kg_service": "グラフサービス",
    "llm_service": "LLMサービス",
    "storage": "データ層",
    "sqlite": "SQLite",
    "memobase": "MemoBase",
    "llm": "LLM",
}

create_architecture_diagram("architecture_zh", "MindPeek System Architecture (中文)", lang_zh)
create_architecture_diagram("architecture_en", "MindPeek System Architecture (English)", lang_en)
create_architecture_diagram("architecture_ja", "MindPeek System Architecture (日本語)", lang_ja)

print("Architecture diagrams generated successfully!")
