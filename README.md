# MindPeek - 懂你的 AI 伙伴 🎯

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.9+-blue.svg" alt="Python">
  <img src="https://img.shields.io/badge/Vue-3-green.svg" alt="Vue">
  <img src="https://img.shields.io/badge/License-GPL--3.0-orange.svg" alt="License">
  <img src="https://img.shields.io/badge/LangGraph-Enabled-purple.svg" alt="LangGraph">
</p>

> *MindPeek 不是普通的聊天机器人 —— 它是一个能够真正理解你的 AI 伙伴。通过多轮对话和先进的 AI Agent 技术，MindPeek 会越来越懂你，成为你不可或缺的智能助手。*

---

**🌐 Language**: [English](README_en.md) | [中文](README.md) | [日本語](README_ja.md)

---

## ✨ 核心亮点

MindPeek 将你的对话转化为对你的深度理解：

| 🔮 智能体 | 💡 功能 | 🎯 价值 |
|---------|--------|---------|
| **FeatureDiscovery Agent** | 自主发现你的性格、习惯、偏好 | 无需手动输入，AI 自动学习 |
| **LatentIntent Agent** | 识别你的隐性需求和潜在意图 | 比你更早知道你需要什么 |
| **CorrelationAgent** | 发现特征之间的关联和推断 | 构建完整的用户画像网络 |
| **DeepThink Agent** | 深度心理分析 | 探索你言行背后的心理动机 |

## 🚀 为什么选择 MindPeek？

### 🤖 多 Agent 协作系统
基于 LangGraph 构建的智能 Agent 网络，多个专业 Agent 协同工作：
- **异步处理**：对话流畅不卡顿，后台任务自动执行
- **智能路由**：自动判断何时使用个性化，何时通用回复
- **并行分析**：特征提取、关联分析、需求发现同时进行

### 🧠 比你更懂你自己
- **主动学习**：通过对话自动发现你的 MBTI、行为习惯、兴趣爱好
- **隐性需求挖掘**：发现你没说出口但实际需要的东西
- **动态画像**：随着对话深入，画像越来越精确

### 🔄 智能特征衰减机制
- **LLM 评估稳定性**：每个特征由大模型判断其稳定程度
- **个性化衰减曲线**：稳定特征衰减慢，易变特征衰减快
- **懒更新策略**：只在用户访问时计算衰减，减少数据库写入
- **对数衰减函数**：
  - 稳定期内完全不衰减
  - 稳定期后开始缓慢对数衰减
  - 最终趋于最低阈值（0.3）

![衰减函数示意图](https://trae-api-cn.mchost.guru/api/ide/v1/text_to_image?prompt=衰减函数图表，X轴表示时间（天数），Y轴表示置信度（0-1）。图表包含：1. 稳定期（0-30天）：置信度保持在0.9不变；2. 对数衰减期（30天后）：置信度缓慢下降；3. 最低阈值线：置信度最终趋于0.3。使用深蓝色线条，专业数据可视化风格，清晰的坐标轴标签，中文标注。&image_size=landscape_16_9)

### 🔗 社会关系感知
- 自动识别对话中的人物关系（家人、朋友、同事等）
- 理解你的人际互动模式
- 构建完整的社会关系图谱

### 🎯 个人信息提取
- 自动提取用户姓名、职业、居住地等基本信息
- 识别并记录用户透露的个人情况
- 智能分析并存储社会关系网络

### ⚡ 生产级性能
- 异步任务队列，最多 3 个 Agent 并行执行
- 用户对话零延迟体验
- 后台任务自动调度

### 💾 双重存储架构
- **SQLite 本地存储**：核心用户数据、对话历史、特征信息
- **MemoBase 远程同步**：跨设备特征同步，云端备份

## 📊 系统架构

```
┌──────────────────────────────────────────────────────────────────┐
│                         MindPeek 前端                            │
│    💬 聊天  │  👤 画像  │  🔗 知识图谱  │  ✨ 特征  │  ⚙️ 设置   │
└──────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌──────────────────────────────────────────────────────────────────┐
│                     🤖 LangGraph Orchestrator                     │
│  ┌────────────┐  ┌────────────┐  ┌────────────┐  ┌───────────┐ │
│  │  Feature   │  │  Latent    │  │Correlation │  │ DeepThink │ │
│  │ Discovery  │  │   Intent   │  │   Agent    │  │   Agent   │ │
│  └────────────┘  └────────────┘  └────────────┘  └───────────┘ │
└──────────────────────────────────────────────────────────────────┘
                                │
        ┌───────────────────────┼───────────────────────┐
        ▼                       ▼                       ▼
┌───────────────┐    ┌───────────────┐    ┌───────────────┐
│   💾 SQLite   │    │  📡 MemoBase  │    │  🧠 LLM       │
│   本地存储    │    │   远程存储    │    │  (DeepSeek等)  │
└───────────────┘    └───────────────┘    └───────────────┘
                                │
                                ▼
                    ┌───────────────────────┐
                    │  🧠 知识图谱           │
                    │  预定义心理学知识库   │
                    │  + 实时推理引擎       │
                    └───────────────────────┘
```

## 🛠️ 技术栈

### 后端
- **FastAPI** - 高性能异步 Web 框架
- **LangGraph** - 多 Agent 编排框架
- **SQLAlchemy** - 异步 ORM
- **知识图谱** - 预定义心理学知识库 + 实时推理
- **Pydantic** - 数据验证
- **vis-network** - 图可视化

### 前端
- **Vue 3** - 组合式 API
- **Element Plus** - UI 组件库
- **Pinia** - 状态管理
- **ECharts** - 数据可视化
- **vis-network** - 知识图谱可视化

### AI 能力
- **OpenAI 兼容接口** - 支持所有主流大模型
- **DeepSeek** - 默认配置
- **通义千问 / 智谱 AI / Ollama** - 全部支持

## 🚀 快速开始

### 1. 安装依赖

```bash
cd MindPeek
pip install -r requirements.txt
cd frontend && npm install
```

### 2. 配置系统

```bash
copy config\config.example.json config\config.json
```

编辑 `config/config.json`，填入你的配置：

```json
{
    "llm_providers": {
        "deepseek": {
            "enabled": true,
            "api_key": "your_api_key",
            "api_url": "https://api.deepseek.com/v1",
            "model": "deepseek-chat"
        }
    },
    "default_provider": "deepseek",
    "memo_base": {
        "enabled": true,
        "project_url": "http://your-memobase:8019",
        "api_key": "your_memobase_key"
    },
    "agent": {
        "max_concurrent_agents": 3,
        "comment": "控制并行Agent的最大数量，根据服务器性能调整，建议值为1-5"
    }
}
```

### 3. 启动服务

```bash
# 后端 (终端 1)
cd MindPeek
python -m uvicorn main:app --host 0.0.0.0 --port 8000

# 前端 (终端 2)
cd MindPeek/frontend
npm run dev
```

### 4. 开始探索

- 🌐 前端界面：http://localhost:3000
- 📖 API 文档：http://localhost:8000/docs

## 📁 项目结构

```
MindPeek/
├── main.py                     # FastAPI 入口
├── requirements.txt            # Python 依赖
├── config/
│   ├── config.json             # 运行时配置
│   └── config.example.json     # 配置模板
├── backend/
│   ├── api/
│   │   └── routes.py           # API 路由
│   ├── models/
│   │   ├── database.py         # 数据库模型
│   │   └── schemas.py          # Pydantic 模型
│   ├── services/
│   │   ├── llm_provider.py     # 多 Provider 支持
│   │   ├── profile_service.py  # 用户画像服务
│   │   └── memo_base_service.py # 远程存储
│   ├── agents/
│   │   ├── chat_graph.py       # 🤖 LangGraph 聊天图
│   │   ├── feature_discovery.py # 🔮 特征发现 Agent
│   │   ├── personal_info_agent.py # 🎯 个人信息提取
│   │   ├── async_orchestrator.py # ⚡ 异步任务编排
│   │   └── agent_engine.py     # Agent 引擎
│   ├── services/
│   │   ├── profile_service.py  # 用户画像服务
│   │   ├── feature_merger.py   # ✨ 特征智能合并
│   │   ├── llm_provider.py     # 多 Provider 支持
│   │   └── memo_base_service.py # 远程存储
│   └── knowledge_graph/
│       └── graph.py            # 🔗 知识图谱（实时推理）
├── frontend/
│   ├── src/
│   │   ├── views/              # 页面组件
│   │   ├── stores/             # Pinia 状态
│   │   ├── api/                # API 调用
│   │   └── router/             # 路由配置
│   └── package.json
└── data/
    └── permir.db               # SQLite 数据库
```

## 🎨 功能展示

### 💬 智能对话
- 多轮对话，自动上下文理解
- 个性化回复，根据你的特征定制
- 深度思考模式可选
- 流式输出，实时显示思考过程

### 👤 用户画像
- MBTI 性格分析
- 大五人格雷达图
- 行为习惯洞察
- 隐性需求发现
- 个人信息追踪（姓名、职业、居住地等）
- 社会关系管理

### 🔗 知识图谱
- 基于预定义心理学知识库的实时推理
- 特征关联可视化
- 动态推断潜在特征

### 🔮 Agent 工作台
- 实时查看 Agent 任务状态
- 异步任务管理
- 洞察报告

### 🔍 特征管理
- 智能特征去重和合并
- 特征搜索功能，快速定位
- 无限滚动加载，流畅体验
- 特征验证次数追踪
- 特征衰减可视化

## 📜 License

GNU General Public License v3.0 (GPL-3.0)

See [LICENSE](LICENSE) for full license text.

---

<p align="center">
  <strong>MindPeek</strong> - 让 AI 真正理解你
</p>
