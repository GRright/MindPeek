# MindPeek - Your AI Partner That Understands You 🎯

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.9+-blue.svg" alt="Python">
  <img src="https://img.shields.io/badge/Vue-3-green.svg" alt="Vue">
  <img src="https://img.shields.io/badge/License-GPL--3.0-orange.svg" alt="License">
  <img src="https://img.shields.io/badge/LangGraph-Enabled-purple.svg" alt="LangGraph">
</p>

> *MindPeek is not an ordinary chatbot — it's an AI partner that truly understands you. Through multi-turn conversations and advanced AI Agent technology, MindPeek gets to know you better over time, becoming an indispensable intelligent assistant.*

---

**🌐 Language**: [English](README_en.md) | [中文](README.md) | [日本語](README_ja.md)

---

## ✨ Key Features

MindPeek transforms your conversations into deep self-understanding:

| 🔮 Agent | 💡 Function | 🎯 Value |
|---------|--------|---------|
| **FeatureDiscovery Agent** | Auto-discover personality, habits, preferences | No manual input, AI learns automatically |
| **LatentIntent Agent** | Identify hidden needs and potential intentions | Know what you need before you do |
| **Relationship Agent** | Discover your social network | Understand your interpersonal patterns |
| **DeepThink Agent** | Deep psychological analysis | Explore the psychology behind your words |

## 🚀 Why Choose MindPeek?

### 🤖 Multi-Agent Collaboration System
Built on LangGraph, an intelligent Agent network where multiple specialized Agents work together:
- **Async Processing**: Smooth conversations, background tasks auto-execute
- **Smart Routing**: Auto-decide when to use personalization vs. general responses
- **Parallel Analysis**: Feature extraction, correlation analysis, and need discovery run simultaneously

### 🧠 Knows You Better Than You Know Yourself
- **Active Learning**: Auto-discover your MBTI, behavioral habits, interests through conversation
- **Hidden Need Mining**: Discover things you didn't say but actually need
- **Dynamic Profiling**: Profile becomes more accurate as conversations deepen

### 🔗 Social Relationship Awareness
- Auto-recognize people mentioned in conversations (family, friends, colleagues, etc.)
- Understand your interpersonal interaction patterns
- Build a complete social relationship graph

### ⚡ Production-Grade Performance
- Async task queue, up to 3 Agents running in parallel
- Zero-latency user conversation experience
- Background task auto-scheduling

## 📊 System Architecture

```
┌──────────────────────────────────────────────────────────────────┐
│                         MindPeek Frontend                        │
│    💬 Chat  │  👤 Profile  │  🔗 Knowledge Graph  │  ✨ Features │
└──────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌──────────────────────────────────────────────────────────────────┐
│                     🤖 LangGraph Orchestrator                     │
│  ┌────────────┐  ┌────────────┐  ┌────────────┐  ┌───────────┐ │
│  │  Feature   │  │  Latent    │  │Relationship│  │ DeepThink │ │
│  │ Discovery  │  │   Intent   │  │  Agent     │  │   Agent   │ │
│  └────────────┘  └────────────┘  └────────────┘  └───────────┘ │
└──────────────────────────────────────────────────────────────────┘
                                │
        ┌───────────────────────┼───────────────────────┐
        ▼                       ▼                       ▼
┌───────────────┐    ┌───────────────┐    ┌───────────────┐
│   💾 SQLite   │    │  📡 MemoBase  │    │  🧠 LLM       │
│   Local Store │    │  Remote Store │    │  (DeepSeek等)  │
└───────────────┘    └───────────────┘    └───────────────┘
```

## 🛠️ Tech Stack

### Backend
- **FastAPI** - High-performance async web framework
- **LangGraph** - Multi-Agent orchestration framework
- **SQLAlchemy** - Async ORM
- **NetworkX** - Knowledge graph
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

Edit `config/config.json` with your settings:

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
        "comment": "Controls the maximum number of parallel Agents, adjust based on server performance, recommended value 1-5"
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
│   └── config.example.json    # Configuration template
├── backend/
│   ├── api/
│   │   └── routes.py          # API routes
│   ├── models/
│   │   ├── database.py         # Database models
│   │   └── schemas.py         # Pydantic models
│   ├── services/
│   │   ├── llm_provider.py    # Multi-Provider support
│   │   ├── profile_service.py # User profiling service
│   │   └── memo_base_service.py # Remote storage
│   ├── agents/
│   │   ├── chat_graph.py      # 🤖 LangGraph chat graph
│   │   ├── feature_discovery.py # 🔮 Feature discovery Agent
│   │   ├── async_orchestrator.py # ⚡ Async task orchestration
│   │   └── agent_engine.py    # Agent engine
│   └── knowledge_graph/
│       └── graph.py           # 🔗 Knowledge graph
├── frontend/
│   ├── src/
│   │   ├── views/             # Page components
│   │   ├── stores/            # Pinia state
│   │   ├── api/               # API calls
│   │   └── router/            # Router config
│   └── package.json
└── data/
    └── permir.db              # SQLite database
```

## 🎨 Features

### 💬 Intelligent Chat
- Multi-turn conversation with automatic context understanding
- Personalized responses tailored to your profile
- Optional deep thinking mode

### 👤 User Profile
- MBTI personality analysis
- Big Five personality radar chart
- Behavioral habit insights
- Hidden need discovery

### 🔗 Knowledge Graph
- Feature correlation visualization
- Social relationship network
- Dynamic updated graph

### 🔮 Agent Dashboard
- Real-time Agent task status
- Async task management
- Insight reports

## 📜 License

GNU General Public License v3.0 (GPL-3.0)

See [LICENSE](LICENSE) for full license text.

---

<p align="center">
  <strong>MindPeek</strong> - Let AI Truly Understand You
</p>
