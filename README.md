# perMIR - 用户画像生成系统

基于LLM的多轮对话用户画像生成系统。用户通过与AI聊天，系统自动分析并生成用户画像，包括性格类型、行为习惯、潜在想法等隐性特征。

## 项目简介

**perMIR** 能做什么：
- 从多轮对话中提取用户的隐性特征（MBTI、大五人格、行为习惯、潜在想法）
- 随着对话深入，自动关联和更新用户画像
- 图形化展示用户画像，支持实时更新

**典型使用场景**：
- 用户研究：了解用户的真实性格和潜在需求
- 个性化推荐：基于用户画像提供个性化服务
- 客服系统：通过对对话分析用户特征，提供更好的服务

## 支持的大模型

| 提供者 | 模型 | 说明 |
|--------|------|------|
| **OpenRouter** | stepfun/step-3.5-flash:free | 免费模型，默认使用 |
| 通义千问 | qwen-turbo | 国产大模型 |
| 文心一言 | ernie-bot | 国产大模型 |
| 智谱AI | glm-4 | 国产大模型 |
| Ollama | llama3, qwen | 本地大模型 |
| OpenAI | gpt-4, gpt-3.5 | OpenAI官方模型 |

## 环境要求

- Python 3.9+
- Node.js 18+
- 网络连接（调用LLM需要）

## 安装步骤

### 1. 克隆项目

```bash
cd c:\Users\Administrator\Desktop\perMIR
```

### 2. 安装后端依赖

```bash
pip install -r requirements.txt
```

### 3. 安装前端依赖

```bash
cd frontend
npm install
cd ..
```

## 配置API Key

> ⚠️ **注意**：`config/config.json` 包含敏感信息，已从版本控制中排除。
> 请复制 `config/config.example.json` 作为模板进行配置。

### 方式一：使用内置的OpenRouter（推荐）

OpenRouter 提供免费模型 `stepfun/step-3.5-flash:free`，适合测试使用。

```bash
# 复制配置文件
copy config\config.example.json config\config.json
```

编辑 `config/config.json`，填入你的API Key：

```json
{
    "llm_providers": {
        "openrouter": {
            "enabled": true,
            "api_key": "sk-or-v1-你的key",
            "api_url": "https://openrouter.ai/api/v1/chat/completions",
            "model": "stepfun/step-3.5-flash:free"
        }
    },
    "default_provider": "openrouter"
}
```

**获取OpenRouter API Key**：
1. 访问 https://openrouter.ai/keys
2. 注册/登录账号
3. 创建新的API Key
4. 将Key填入配置文件

### 方式二：使用其他模型

**通义千问**：
```json
{
    "llm_providers": {
        "qwen": {
            "enabled": true,
            "api_key": "你的阿里云DashScope API Key",
            "model": "qwen-turbo"
        }
    },
    "default_provider": "qwen"
}
```

**文心一言**：
```json
{
    "llm_providers": {
        "ernie": {
            "enabled": true,
            "api_key": "你的百度文心一言 API Key",
            "secret_key": "你的百度Secret Key"
        }
    },
    "default_provider": "ernie"
}
```

## 启动服务

### 启动后端

```bash
cd c:\Users\Administrator\Desktop\perMIR
python -m uvicorn main:app --host 0.0.0.0 --port 8000
```

后端启动后访问：
- API文档：http://localhost:8000/docs
- 健康检查：http://localhost:8000/health

### 启动前端

新开一个终端：

```bash
cd c:\Users\Administrator\Desktop\perMIR\frontend
npm run dev
```

前端启动后访问：http://localhost:3000

## 使用流程

1. **打开前端界面**：访问 http://localhost:3000

2. **进入聊天页面**：在左侧导航点击"聊天分析"

3. **输入用户ID和消息**：开始与AI对话

4. **查看用户画像**：
   - 点击左侧"用户画像"查看图形化展示
   - 支持雷达图、关系图、饼图等多种可视化方式
   - 画像会随着对话深入自动更新

5. **查看知识图谱**：点击"知识图谱"查看特征关联关系

## 项目结构

```
perMIR/
├── main.py                    # 后端入口
├── requirements.txt          # Python依赖
├── config/
│   └── config.json           # 配置文件
├── backend/
│   ├── api/routes.py         # API路由
│   ├── core/config.py        # 配置加载
│   ├── models/               # 数据模型
│   │   ├── database.py       # 数据库模型
│   │   └── schemas.py        # Pydantic模型
│   ├── services/
│   │   ├── llm_provider.py   # LLM提供者
│   │   └── profile_service.py# 画像服务
│   ├── agents/
│   │   └── agent_engine.py   # 多Agent引擎
│   └── knowledge_graph/
│       └── graph.py          # 知识图谱
├── frontend/                  # Vue 3前端
│   ├── src/
│   │   ├── views/            # 页面组件
│   │   ├── stores/          # Pinia状态
│   │   ├── api/              # API调用
│   │   └── router/           # 路由配置
│   ├── package.json
│   └── vite.config.js
├── tests/                     # 测试文件
│   └── test_core.py
└── data/                      # 数据存储
    └── permir.db              # SQLite数据库
```

## API接口

### 发送消息并提取特征
```bash
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "user123",
    "message": "我周末喜欢宅在家里看书",
    "extract_features": true
  }'
```

### 获取用户画像
```bash
curl http://localhost:8000/api/profile/user123
```

### 获取知识图谱
```bash
curl http://localhost:8000/api/knowledge-graph/user123
```

### 配置LLM
```bash
curl -X POST http://localhost:8000/api/llm/config \
  -H "Content-Type: application/json" \
  -d '{
    "provider": "openrouter",
    "api_key": "your-api-key"
  }'
```

## 主要业务逻辑

### 对话处理流程

```
用户发送消息
    │
    ▼
保存对话记录到数据库
    │
    ▼
多Agent并行分析（4个Agent同时工作）
    ├── MBTI分析Agent → 推断性格类型
    ├── 大五人格Agent → 评估五因素得分
    ├── 行为习惯Agent → 识别日常习惯
    └── 隐性意图Agent → 分析潜在想法
    │
    ▼
特征提取与融合
    │
    ▼
知识图谱关联推理
    ├── 特征关联（如：内向型 → 社交回避）
    └── 冲突检测（如：矛盾的特征）
    │
    ▼
更新用户画像
    │
    ▼
返回结果给前端图形化展示
```

### 特征类型说明

| 类型 | 说明 | 示例 |
|------|------|------|
| MBTI | 16种性格类型 | INTP, ENFP, ISTJ |
| 大五人格 | 五因素模型评分 | 开放性: 75, 尽责性: 80 |
| 行为习惯 | 日常行为模式 | 作息: 夜猫子, 消费: 理性 |
| 潜在想法 | 未明说的需求 | 社交回避, 追求安全感 |

## 技术栈

| 层级 | 技术 |
|------|------|
| 后端框架 | FastAPI + Uvicorn |
| 数据库 | SQLite + SQLAlchemy |
| 图计算 | NetworkX |
| 前端框架 | Vue 3 + Vite |
| UI组件 | Element Plus |
| 图表库 | ECharts |
| 状态管理 | Pinia |

## 运行测试

```bash
python tests/test_core.py
```

## 常见问题

**Q: 前端白屏怎么办？**
A: 确保已执行 `npm install`，然后重新执行 `npm run dev`

**Q: 后端启动失败？**
A: 检查Python依赖是否安装完整，端口8000是否被占用

**Q: LLM调用失败？**
A: 检查config.json中的api_key是否正确，网络是否正常

**Q: 如何切换模型？**
A: 修改config/config.json中的default_provider和对应的模型配置

## License

MIT
