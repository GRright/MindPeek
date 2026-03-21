# MindPeek - Intelligent User Profile Generation System

A multi-turn conversation-based user profile generation system powered by LLM. Through natural dialogue, MindPeek can deeply analyze users' implicit characteristics, including personality types, behavioral habits, hidden thoughts, etc., providing powerful support for user research and personalized services.

---

**🌐 Language / 语言 / 言語**: [English](README_en.md) | [中文](README.md) | [日本語](README_ja.md)

---

## Key Features

- **Intelligent Feature Extraction**: Automatically identify MBTI personality types, Big Five personality traits, behavioral habits, hidden thoughts, etc. from multi-turn conversations
- **Real-time Profile Updates**: As conversations deepen, the system continuously learns and updates user profiles
- **Knowledge Graph Visualization**: Display the relationships between user characteristics in a graphical format
- **Multi-backend Storage Support**: Supports SQLite local storage and MemoBase remote storage
- **OpenAI Compatible Interface**: Supports any LLM service with OpenAI-compatible API
- **Modern Frontend Interface**: Dark theme interface inspired by Open WebUI

## Tech Stack

### Backend

- **FastAPI** - High-performance Python Web framework
- **SQLAlchemy** - Async ORM database access
- **httpx** - Async HTTP client
- **Pydantic** - Data validation and model definition
- **NetworkX** - Knowledge graph construction

### Frontend

- **Vue 3** - Progressive JavaScript framework
- **Element Plus** - UI component library
- **Pinia** - State management
- **vis-network** - Knowledge graph visualization
- **ECharts** - Data visualization charts

### Supported LLMs

This system connects to LLMs through OpenAI-compatible interfaces, supporting:

- DeepSeek (default configuration)
- Tongyi Qianwen
- Zhipu AI
- Ollama (local models)
- OpenAI GPT series
- Any service providing OpenAI-compatible API

## Requirements

- Python 3.9+
- Node.js 18+
- Internet connection (required for LLM calls)

## Quick Start

### 1. Install Dependencies

```bash
cd MindPeek
pip install -r requirements.txt
cd frontend
npm install
cd ..
```

### 2. Configure the System

> :warning: **Important**: Copy `config.example.json` to `config.json` and fill in your configuration information.

Copy and edit the configuration template:

```bash
copy config\config.example.json config\config.json
```

Edit `config/config.json` with your LLM and MemoBase information:

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

**Configuration Notes:**
- `api_key`: Your API key (local LLM deployments can use any string like `dummy_key`)
- `api_url`: LLM/MemoBase service address
- `model`: Model name to use

### 3. Start Services

Start backend (Terminal 1):

```bash
cd MindPeek
python -m uvicorn main:app --host 0.0.0.0 --port 8000
```

Start frontend (Terminal 2):

```bash
cd MindPeek/frontend
npm run dev
```

### 4. Access the System

- Frontend UI: http://localhost:3000
- API Docs: http://localhost:8000/docs
- Health Check: http://localhost:8000/health

## Configuration Details

### LLM Provider Configuration

| Parameter | Description | Example |
|-----------|-------------|---------|
| `enabled` | Whether to enable this provider | `true` |
| `api_key` | API key (use dummy_key for local deployment) | `dummy_key` |
| `api_url` | API address (OpenAI-compatible format) | `http://172.16.5.147:8000/v1` |
| `model` | Model name | `deepseek-chat` |
| `temperature` | Generation temperature (0-1) | `0.7` |
| `max_tokens` | Maximum tokens | `2000` |

### MemoBase Configuration

MemoBase is used for remote storage of user profiles and conversation history:

| Parameter | Description | Example |
|-----------|-------------|---------|
| `enabled` | Whether to enable MemoBase | `true` |
| `project_url` | MemoBase service address | `http://172.16.5.147:8019` |
| `api_key` | MemoBase API Key | `GdyztMemobase2025` |

## Features

### Chat Analysis

Have natural conversations with AI in the chat interface. The system analyzes conversation content in real-time and extracts user characteristics.

### User Profile

View graphical user profiles including:
- MBTI personality quadrant analysis
- Feature radar chart
- Confidence display

### Knowledge Graph

Display the relationships between characteristics as nodes and edges, helping understand the intrinsic connections between user characteristics.

### Feature Management

View, filter, and manage extracted user characteristics.

## Project Structure

```
MindPeek/
├── main.py                     # FastAPI application entry
├── requirements.txt            # Python dependencies
├── config/
│   ├── config.json             # Runtime configuration file
│   └── config.example.json    # Configuration template
├── backend/
│   ├── api/
│   │   └── routes.py          # API route definitions
│   ├── core/
│   │   └── config.py          # Configuration management module
│   ├── models/
│   │   ├── database.py         # SQLAlchemy models
│   │   └── schemas.py         # Pydantic models
│   ├── services/
│   │   ├── llm_provider.py    # LLM provider (multi-provider support)
│   │   ├── profile_service.py  # User profile service
│   │   └── memo_base_service.py # MemoBase storage service
│   ├── agents/
│   │   └── agent_engine.py    # Multi-agent coordination engine
│   └── knowledge_graph/
│       └── graph.py           # Knowledge graph module
├── frontend/                   # Vue 3 frontend
│   ├── src/
│   │   ├── views/             # Page components
│   │   ├── stores/            # Pinia state management
│   │   ├── api/               # API call wrappers
│   │   └── router/            # Vue Router configuration
│   └── package.json
└── data/                       # Data storage directory
    └── permir.db              # SQLite database
```

## License

GNU General Public License v3.0 (GPL-3.0)

See [LICENSE](LICENSE) for full license text.
