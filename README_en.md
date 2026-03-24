# MindPeek - Your AI Partner Who Understands You 🎯

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.9+-blue.svg" alt="Python">
  <img src="https://img.shields.io/badge/Vue-3-green.svg" alt="Vue">
  <img src="https://img.shields.io/badge/License-GPL--3.0-orange.svg" alt="License">
  <img src="https://img.shields.io/badge/LangGraph-Enabled-purple.svg" alt="LangGraph">
</p>

> *MindPeek is not an ordinary chatbot —— it's an AI partner that truly understands you. Through multi-turn conversations and advanced AI Agent technology, MindPeek gets to know you better over time, becoming an indispensable intelligent assistant.*

---

**🌐 Language**: [English](README_en.md) | [中文](README.md) | [日本語](README_ja.md)

---

## ✨ Core Features

MindPeek transforms your conversations into deep understanding of you:

| 🔮 Agent | 💡 Function | 🎯 Value |
|----------|-------------|-----------|
| **FeatureDiscovery Agent** | Automatically discover your personality, habits, preferences | No manual input needed, AI learns automatically |
| **LatentIntent Agent** | Identify your hidden needs and latent intentions | Know what you need before you do |
| **CorrelationAgent** | Discover correlations between features | Build a complete user profile network |
| **DeepThink Agent** | Deep psychological analysis | Explore the psychology behind your words |

## 🚀 Why Choose MindPeek?

### 🤖 Multi-Agent Collaboration System
Intelligent Agent network built on LangGraph, with multiple specialized agents working together:
- **Async Processing**: Smooth conversations, background tasks execute automatically
- **Smart Routing**: Automatically decide when to use personalization vs. general responses
- **Parallel Analysis**: Feature extraction, correlation analysis, and need discovery run simultaneously

### 🧠 Knows You Better Than You Know Yourself
- **Active Learning**: Automatically discover your MBTI, behavioral habits, and interests through conversation
- **Hidden Need Mining**: Discover what you don't say but actually need
- **Dynamic Profiling**: Profile becomes more accurate as conversations deepen

### 🔄 Intelligent Feature Decay Mechanism
- **LLM-Evaluated Stability**: Each feature's stability is judged by the large model
- **Personalized Decay Curve**: Stable features decay slowly, volatile features decay fast
- **Lazy Update Strategy**: Calculate decay only when user accesses, reducing database writes
- **Logarithmic Decay Function**:
  - No decay during stability period
  - Slow logarithmic decay after stability period
  - Eventually converges to minimum threshold (0.3)

![Decay Function Diagram](https://trae-api-cn.mchost.guru/api/ide/v1/text_to_image?prompt=Decay%20function%20chart%2C%20X-axis%20represents%20time%20%28days%29%2C%20Y-axis%20represents%20confidence%20%280-1%29.%20The%20chart%20includes%3A%201.%20Stability%20period%20%280-30%20days%29%3A%20confidence%20remains%20constant%20at%200.9%3B%202.%20Logarithmic%20decay%20period%20%28after%2030%20days%29%3A%20confidence%20slowly%20decreases%3B%203.%20Minimum%20threshold%20line%3A%20confidence%20eventually%20approaches%200.3.%20Use%20dark%20blue%20lines%2C%20professional%20data%20visualization%20style%2C%20clear%20axis%20labels%2C%20English%20labels.&image_size=landscape_16_9)

### 🔗 Social Relationship Awareness
- Automatically identify people mentioned in conversations (family, friends, colleagues, etc.)
- Understand your interpersonal interaction patterns
- Build a complete social relationship map

### ⚡ Production-Grade Performance
- Async task queue with up to 3 agents executing in parallel
- Zero-latency user conversation experience
- Automatic background task scheduling

### 💾 Dual Storage Architecture
- **SQLite Local Storage**: Core user data, conversation history, feature information
- **MemoBase Remote Sync**: Cross-device feature sync, cloud backup

## 📊 System Architecture

```
┌──────────────────────────────────────────────────────────────────┐
│                         MindPeek Frontend                        │
│    💬 Chat  │  👤 Profile  │  🔗 Knowledge Graph  │  ✨ Features  │  ⚙️ Settings   │
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
│   Local Store │    │   Remote Sync │    │  (DeepSeek等)  │
└───────────────┘    └───────────────┘    └───────────────┘
                                │
                                ▼
                    ┌───────────────────────┐
                    │  🧠 Knowledge Graph   │
                    │  Predefined Psychology│
                    │  Knowledge Base +     │
                    │  Real-time Inference  │
                    └───────────────────────┘
```

## 🛠️ Tech Stack

### Backend
- **FastAPI** - High-performance async web framework
- **LangGraph** - Multi-Agent orchestration framework
- **SQLAlchemy** - Async ORM
- **Knowledge Graph** - Predefined psychology knowledge base + real-time inference
- **Pydantic** - Data validation

### Frontend
- **Vue 3** - Composition API
- **Element Plus** - UI component library
- **Pinia** - State management
- **ECharts** - Data visualization
- **vis-network** - Knowledge graph visualization

### AI Capabilities
- **OpenAI Compatible Interface** - Supports all major LLMs
- **DeepSeek** - Default configuration
- **Qwen / Zhipu AI / Ollama** - All supported

## 🚀 Quick Start

### 1. Install Dependencies

```bash
cd MindPeek
pip install -r requirements.txt
cd frontend && npm install
```

### 2. Configure System

```bash
copy config\config.example.json config\config.json
```

Edit `config/config.json` with your configuration:

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
        "comment": "Max concurrent agents, adjust based on server performance, recommended 1-5"
    }
}
```

### 3. Start Services

```bash
# Backend (Terminal 1)
cd MindPeek
python -m uvicorn main:app --host 0.0.0.0 --port 8000

# Frontend (Terminal 2)
cd MindPeek/frontend
npm run dev
```

### 4. Start Exploring

- 🌐 Frontend: http://localhost:3000
- 📖 API Docs: http://localhost:8000/docs

## 📁 Project Structure

```
MindPeek/
├── main.py                     # FastAPI entry point
├── requirements.txt            # Python dependencies
├── config/
│   ├── config.json             # Runtime configuration
│   └── config.example.json     # Configuration template
├── backend/
│   ├── api/
│   │   └── routes.py           # API routes
│   ├── models/
│   │   ├── database.py         # Database models
│   │   └── schemas.py          # Pydantic models
│   ├── services/
│   │   ├── llm_provider.py     # Multi-provider support
│   │   ├── profile_service.py  # User profiling service
│   │   └── memo_base_service.py # Remote storage
│   ├── agents/
│   │   ├── chat_graph.py       # 🤖 LangGraph chat graph
│   │   ├── feature_discovery.py # 🔮 Feature discovery agent
│   │   ├── async_orchestrator.py # ⚡ Async task orchestration
│   │   └── agent_engine.py     # Agent engine
│   └── knowledge_graph/
│       └── graph.py           # 🔗 Knowledge graph (real-time inference)
├── frontend/
│   ├── src/
│   │   ├── views/             # Page components
│   │   ├── stores/            # Pinia state
│   │   ├── api/               # API calls
│   │   └── router/            # Route configuration
│   └── package.json
└── data/
    └── permir.db              # SQLite database
```

## 🎨 Features

### 💬 Smart Chat
- Multi-turn conversations with automatic context understanding
- Personalized responses based on your features
- Optional deep thinking mode

### 👤 User Profile
- MBTI personality analysis
- Big Five personality radar chart
- Behavioral habit insights
- Hidden need discovery

### 🔗 Knowledge Graph
- Real-time inference based on predefined psychology knowledge base
- Feature correlation visualization
- Dynamic inference of potential features

### 🔮 Agent Workbench
- View agent task status in real-time
- Async task management
- Insight reports

## 📜 License

GNU General Public License v3.0 (GPL-3.0)

See [LICENSE](LICENSE) for full license text.

---

<p align="center">
  <strong>MindPeek</strong> - Let AI truly understand you
</p>
