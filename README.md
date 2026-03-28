# MindPeek - 懂你的 AI 伙伴 🎯

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.9+-blue.svg" alt="Python">
  <img src="https://img.shields.io/badge/Vue-3-green.svg" alt="Vue">
  <img src="https://img.shields.io/badge/License-GPL--3.0-orange.svg" alt="License">
  <img src="https://img.shields.io/badge/LangGraph-Enabled-purple.svg" alt="LangGraph">
</p>

<p align="center">
  <strong>让 AI 真正读懂人心</strong>
</p>

<p align="center">
  <a href="README_en.md">English</a> | <a href="README.md">中文</a> | <a href="README_ja.md">日本語</a>
</p>

---

## ✨ 核心亮点

### 🧠 智能用户画像

MindPeek 通过 LLM 深度解析对话，自动构建持续进化的个人画像：

| 特征维度 | 说明 |
|---------|------|
| **性格特质** | MBTI、大五人格分析 |
| **行为习惯** | 生活习惯、决策模式 |
| **兴趣爱好** | 娱乐偏好、学习方向 |
| **价值观** | 人生观、世界观 |
| **情感状态** | 当前情绪、心理需求 |
| **社会关系** | 人际网络、互动模式 |

### 🔮 AI 行为预测

基于用户画像，预测用户未来的行为和想法：
- **行为预测**：用户可能采取的行动
- **想法预测**：用户可能产生的思考
- **情感预测**：用户可能出现的情绪
- **决策预测**：用户可能做出的选择

### 💬 个性化对话

AI 会根据你的画像提供贴心回复：
- 自然融入你的兴趣和习惯
- 根据你的性格调整语气风格
- 预判你的需求并主动建议
- 像老朋友一样自然对话

---

## 🚀 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
cd frontend && npm install
```

### 2. 配置系统

```bash
copy config\config.example.json config\config.json
```

编辑 `config/config.json`，填入你的 LLM API 配置。

### 3. 启动服务

```bash
python -m uvicorn main:app --host 0.0.0.0 --port 8000
cd frontend && npm run dev
```

### 4. 开始使用

- 🌐 前端界面：http://localhost:3000
- 📖 API 文档：http://localhost:8000/docs

---

## 📊 系统架构

```
┌─────────────────────────────────────────────────────────────────┐
│                        MindPeek 前端                             │
│   💬 聊天  │  👤 画像  │  🔗 知识图谱  │  ✨ 特征  │  ⚙️ 设置   │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                    🤖 LangGraph Orchestrator                     │
│                                                                  │
│   ┌─────────────┐  ┌─────────────┐  ┌─────────────────────────┐  │
│   │   Feature   │  │   Latent    │  │      Correlation       │  │
│   │  Discovery  │  │   Intent    │  │        Agent           │  │
│   │   Agent     │  │   Agent     │  │                        │  │
│   └─────────────┘  └─────────────┘  └─────────────────────────┘  │
│                                                                  │
│   ┌─────────────────────────┐  ┌─────────────────────────────┐  │
│   │        MBTI /           │  │        Prediction           │  │
│   │       BigFive           │  │          Agent              │  │
│   │        Agent            │  │                             │  │
│   └─────────────────────────┘  └─────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                                │
        ┌───────────────────────┼───────────────────────┐
        ▼                       ▼                       ▼
┌─────────────────┐  ┌─────────────────┐  ┌─────────────────────┐
│    💾 SQLite    │  │   📡 MemoBase   │  │       🧠 LLM        │
│    本地存储     │  │    远程存储     │  │   (DeepSeek 等)     │
└─────────────────┘  └─────────────────┘  └─────────────────────┘
```

---

## 🛠️ 技术栈

| 层级 | 技术 |
|-----|------|
| **后端** | FastAPI + LangGraph + SQLAlchemy |
| **前端** | Vue 3 + Element Plus + ECharts |
| **AI** | OpenAI 兼容接口 + Sentence Transformers |
| **存储** | SQLite + MemoBase 云同步 |

---

## 🆕 最新特性

### 智能意图判断
基于 **Embedding 语义理解** 的智能意图分类：
- 混合方法：规则优先 + Embedding 语义判断
- 高性能：90%+ 请求毫秒级响应
- 智能理解：同义词、变体表达精准识别

### 特征衰减机制
![衰减函数示意图](docs/images/decay_function_en.png)

- **稳定期**：特征置信度保持不变
- **衰减期**：对数衰减，最终趋于最小阈值
- **懒更新**：访问时计算，减少数据库写入

---

## 📁 项目结构

```
MindPeek/
├── backend/
│   ├── agents/          # Agent 智能体
│   │   ├── chat_graph.py          # 对话流程
│   │   ├── feature_discovery.py   # 特征发现
│   │   ├── prediction_agent.py    # 行为预测
│   │   └── intent_classifier.py   # 意图分类
│   ├── services/        # 服务层
│   ├── knowledge_graph/ # 知识图谱
│   └── models/          # 数据模型
├── frontend/            # Vue 3 前端
└── config/              # 配置文件
```

---

## 📜 License

[GNU General Public License v3.0](LICENSE)

---

<p align="center">
  <strong>MindPeek</strong> - 让 AI 真正理解你
</p>
