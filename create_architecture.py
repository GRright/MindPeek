import os

def create_architecture_svg(filename, lang):
    svg = f'''<?xml version="1.0" encoding="UTF-8"?>
<svg width="800" height="700" xmlns="http://www.w3.org/2000/svg">
    <style>
        .title {{ font-family: Arial, sans-serif; font-size: 18px; font-weight: bold; }}
        .layer {{ font-family: Arial, sans-serif; font-size: 14px; font-weight: bold; fill: #333; }}
        .node {{ font-family: Arial, sans-serif; font-size: 11px; fill: #333; }}
        .rect {{ fill: #f5f5f5; stroke: #999; stroke-width: 2; rx: 5; ry: 5; }}
        .node-rect {{ fill: #fff; stroke: #666; stroke-width: 1; rx: 3; ry: 3; }}
        .arrow {{ stroke: #333; stroke-width: 2; fill: none; marker-end: url(#arrowhead); }}
    </style>
    <defs>
        <marker id="arrowhead" markerWidth="10" markerHeight="7" refX="9" refY="3.5" orient="auto">
            <polygon points="0 0, 10 3.5, 0 7" fill="#333"/>
        </marker>
    </defs>
    
    <text x="400" y="30" text-anchor="middle" class="title">MindPeek System Architecture</text>
    
    <rect x="50" y="50" width="700" height="120" class="rect"/>
    <text x="400" y="80" text-anchor="middle" class="layer">{lang['frontend']}</text>
    <rect x="80" y="95" width="140" height="60" class="node-rect"/>
    <text x="150" y="130" text-anchor="middle" class="node">{lang['chat']}</text>
    <rect x="240" y="95" width="140" height="60" class="node-rect"/>
    <text x="310" y="130" text-anchor="middle" class="node">{lang['profile']}</text>
    <rect x="400" y="95" width="140" height="60" class="node-rect"/>
    <text x="470" y="130" text-anchor="middle" class="node">{lang['kg']}</text>
    <rect x="560" y="95" width="140" height="60" class="node-rect"/>
    <text x="630" y="130" text-anchor="middle" class="node">{lang['features']}</text>
    
    <line x1="400" y1="170" x2="400" y2="190" class="arrow"/>
    
    <rect x="50" y="200" width="700" height="120" class="rect"/>
    <text x="400" y="230" text-anchor="middle" class="layer">{lang['agents']}</text>
    <rect x="80" y="245" width="140" height="60" class="node-rect"/>
    <text x="150" y="280" text-anchor="middle" class="node">{lang['feature_agent']}</text>
    <rect x="240" y="245" width="140" height="60" class="node-rect"/>
    <text x="310" y="280" text-anchor="middle" class="node">{lang['intent_agent']}</text>
    <rect x="400" y="245" width="140" height="60" class="node-rect"/>
    <text x="470" y="280" text-anchor="middle" class="node">{lang['mbti_agent']}</text>
    <rect x="560" y="245" width="140" height="60" class="node-rect"/>
    <text x="630" y="280" text-anchor="middle" class="node">{lang['prediction_agent']}</text>
    
    <line x1="400" y1="320" x2="400" y2="340" class="arrow"/>
    
    <rect x="50" y="350" width="700" height="120" class="rect"/>
    <text x="400" y="380" text-anchor="middle" class="layer">{lang['services']}</text>
    <rect x="130" y="395" width="140" height="60" class="node-rect"/>
    <text x="200" y="430" text-anchor="middle" class="node">{lang['profile_service']}</text>
    <rect x="310" y="395" width="140" height="60" class="node-rect"/>
    <text x="380" y="430" text-anchor="middle" class="node">{lang['kg_service']}</text>
    <rect x="490" y="395" width="140" height="60" class="node-rect"/>
    <text x="560" y="430" text-anchor="middle" class="node">{lang['llm_service']}</text>
    
    <line x1="400" y1="470" x2="400" y2="490" class="arrow"/>
    
    <rect x="50" y="500" width="700" height="120" class="rect"/>
    <text x="400" y="530" text-anchor="middle" class="layer">{lang['storage']}</text>
    <rect x="130" y="545" width="140" height="60" class="node-rect"/>
    <text x="200" y="580" text-anchor="middle" class="node">{lang['sqlite']}</text>
    <rect x="310" y="545" width="140" height="60" class="node-rect"/>
    <text x="380" y="580" text-anchor="middle" class="node">{lang['memobase']}</text>
    <rect x="490" y="545" width="140" height="60" class="node-rect"/>
    <text x="560" y="580" text-anchor="middle" class="node">{lang['llm']}</text>
</svg>'''
    
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(svg)
    print(f"Created: {filename}")


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

os.makedirs('docs', exist_ok=True)
create_architecture_svg('docs/architecture_zh.svg', lang_zh)
create_architecture_svg('docs/architecture_en.svg', lang_en)
create_architecture_svg('docs/architecture_ja.svg', lang_ja)

print("Architecture diagrams generated successfully!")
