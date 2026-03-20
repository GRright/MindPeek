# MindPeek - 智能用户画像生成系统

基于 LLM 的多轮对话用户画像生成系统。通过自然对话，MindPeek 能够深入分析用户的隐性特征，包括性格类型、行为习惯、潜在想法等，为用户研究和个性化服务提供强大支持。

## 核心特性

- **智能特征提取**：从多轮对话中自动识别 MBTI 性格类型、大五人格特征、行为习惯、潜在想法等
- **实时画像更新**：随着对话深入，系统持续学习和更新用户画像
- **知识图谱可视化**：以图形化方式展示用户特征之间的关联关系
- **多后端存储支持**：支持 SQLite 本地存储和 MemoBase 远程存储
- **OpenAI 兼容接口**：支持对接任何 OpenAI 兼容 API 的大模型服务
- **现代化前端界面**：参考 Open WebUI 风格设计的深色主题界面

## 技术架构

### 后端技术栈

- **FastAPI** - 高性能 Python Web 框架
- **SQLAlchemy** - 异步 ORM 数据库访问
- **httpx** - 异步 HTTP 客户端
- **Pydantic** - 数据验证和模型定义
- **NetworkX** - 知识图谱构建

### 前端技术栈

- **Vue 3** - 渐进式 JavaScript 框架
- **Element Plus** - UI 组件库
- **Pinia** - 状态管理
- **vis-network** - 知识图谱可视化
- **ECharts** - 数据可视化图表

### 支持的大模型

本系统通过 OpenAI 兼容接口连接大模型，支持：

- DeepSeek（默认配置）
- 通义千问
- 智谱 AI
- Ollama（本地模型）
- OpenAI GPT 系列
- 以及任何提供 OpenAI 兼容 API 的服务

## 环境要求

- Python 3.9+
- Node.js 18+
- 网络连接（调用 LLM 需要）

## 快速开始

### 1. 安装依赖

```bash
cd c:\myProject\MindPeek
pip install -r requirements.txt
cd frontend
npm install
cd ..
```

### 2. 配置系统

> ⚠️ **重要提醒**：请从 `config.example.json` 复制该文件并命名为 `config.json`，并填写你自己的配置信息。

复制配置文件模板并编辑：

```bash
copy config\config.example.json config\config.json
```

编辑 `config/config.json`，填入你的 LLM 和 MemoBase 信息：

```json
{
    "llm_providers": {
        "deepseek": {
            "enabled": true,
            "api_key": "your_api_key_here",
            "api_url": "your_llm_api_url_here",
            "model": "your_llm_model_name"
        }
    },
    "default_provider": "deepseek",
    "memo_base": {
        "enabled": true,
        "project_url": "http://your_memobase_server:8019",
        "api_key": "your_memobase_api_key_here"
    }
}
```

**配置说明：**
- `api_key`: 你的 API 密钥（本地部署的 LLM 服务可用任意字符串如 `dummy_key`）
- `api_url`: LLM/MemoBase 服务的地址
- `model`: 使用的模型名称

### 3. 启动服务

启动后端（终端 1）：

```bash
cd c:\myProject\MindPeek
python -m uvicorn main:app --host 0.0.0.0 --port 8000
```

启动前端（终端 2）：

```bash
cd c:\myProject\MindPeek\frontend
npm run dev
```

### 4. 访问系统

- 前端界面：http://localhost:3000
- API 文档：http://localhost:8000/docs
- 健康检查：http://localhost:8000/health

## 配置说明

### LLM Provider 配置

| 参数 | 说明 | 示例 |
|------|------|------|
| `enabled` | 是否启用该 provider | `true` |
| `api_key` | API 密钥（本地部署可用 dummy_key） | `dummy_key` |
| `api_url` | API 地址（OpenAI 兼容格式） | `http://172.16.5.147:8000/v1` |
| `model` | 模型名称 | `deepseek-chat` |
| `temperature` | 生成温度（0-1） | `0.7` |
| `max_tokens` | 最大 token 数 | `2000` |

### MemoBase 配置

MemoBase 用于远程存储用户画像和对话历史：

| 参数 | 说明 | 示例 |
|------|------|------|
| `enabled` | 是否启用 MemoBase | `true` |
| `project_url` | MemoBase 服务地址 | `http://172.16.5.147:8019` |
| `api_key` | MemoBase API Key | `GdyztMemobase2025` |

## 功能模块

### 聊天分析

在聊天界面与 AI 进行自然对话，系统会实时分析对话内容，提取用户特征。

### 用户画像

查看图形化的用户画像，包括：
- MBTI 性格四宫格分析
- 特征雷达图
- 置信度展示

### 知识图谱

以节点和边的形式展示特征之间的关联关系，帮助理解用户特征的内在联系。

### 特征管理

查看、筛选和管理已提取的用户特征。

## 项目结构

```
MindPeek/
├── main.py                     # FastAPI 应用入口
├── requirements.txt            # Python 依赖
├── config/
│   ├── config.json             # 运行时配置文件
│   └── config.example.json    # 配置模板
├── backend/
│   ├── api/
│   │   └── routes.py          # API 路由定义
│   ├── core/
│   │   └── config.py          # 配置管理模块
│   ├── models/
│   │   ├── database.py         # SQLAlchemy 模型
│   │   └── schemas.py         # Pydantic 模型
│   ├── services/
│   │   ├── llm_provider.py    # LLM 提供者（多provider支持）
│   │   ├── profile_service.py  # 用户画像服务
│   │   └── memo_base_service.py # MemoBase 存储服务
│   ├── agents/
│   │   └── agent_engine.py    # 多 Agent 协调引擎
│   └── knowledge_graph/
│       └── graph.py           # 知识图谱模块
├── frontend/                   # Vue 3 前端
│   ├── src/
│   │   ├── views/             # 页面组件
│   │   ├── stores/            # Pinia 状态管理
│   │   ├── api/               # API 调用封装
│   │   └── router/            # Vue Router 配置
│   └── package.json
└── data/                       # 数据存储目录
    └── permir.db              # SQLite 数据库
```

## License

MIT License
