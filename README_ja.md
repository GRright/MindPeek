# MindPeek - あなたのことを理解するAIパートナー 🎯

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.9+-blue.svg" alt="Python">
  <img src="https://img.shields.io/badge/Vue-3-green.svg" alt="Vue">
  <img src="https://img.shields.io/badge/License-GPL--3.0-orange.svg" alt="License">
  <img src="https://img.shields.io/badge/LangGraph-Enabled-purple.svg" alt="LangGraph">
</p>

> *MindPeekは普通のチャットボットではありません — あなたを真に理解するAIパートナーです。多対話を介して、先進的なAI Agent技術により、MindPeekはあなたをますます理解し、不可欠なIntelligentアシスタントになります。*

---

**🌐 Language**: [English](README_en.md) | [中文](README.md) | [日本語](README_ja.md)

---

## ✨ 主な機能

MindPeekはあなたとの対話を深い自己理解に変換します：

| 🔮 Agent | 💡 機能 | 🎯 価値 |
|---------|--------|---------|
| **FeatureDiscovery Agent** | 性格、習慣、偏好を自動発見 | 手動入力不要、AIが自動学習 |
| **LatentIntent Agent** | 隠れたニーズと潜在的な意図を識別 | あなたが知る前に必要なものを把握 |
| **Relationship Agent** | あなたのソーシャルネットワークを発見 | 対人インタラクションパターンを理解 |
| **DeepThink Agent** | 深層心理分析 | あなたの言葉の背後にある心理を探求 |

## 🚀 MindPeekを選ぶ理由？

### 🤖 マルチAgent協調システム
LangGraphに基づいて構築されたIntelligent Agentネットワーク：
- **非同期処理**：スムーズな会話、バックグラウンドタスクが自動実行
- **スマートルーティング**：パーソナライゼーションと汎用応答を自動判断
- **並列分析**：特徴抽出、相関分析、ニーズ発見が同時に実行

### 🧠 自分より自分を理解する
- **能動的学習**：会話を介してMBTI、行動習慣、興rizzを自動発見
- **隠れたニーズの発掘**：言わなかったが実際必要なものを発見
- **動的プロファイリング**：会話が深まるほどプロファイルが正確になる

### 🔗 ソーシャルリレーションシップ認知
- 会話で言及された人物を自動認識（家族、友人、同僚など）
- あなたの対人インタラクションパターンを理解
- 完全なソーシャルリレーションシップグラフを構築

### ⚡ 本番環境レベルのパフォーマンス
- 非同期タスクキュー、最大3つのAgentが並列実行
- ゼロレイテンシーのユーザー会話体験
- バックグラウンドタスクの自動スケジューリング

## 📊 システムアーキテクチャ

```
┌──────────────────────────────────────────────────────────────────┐
│                         MindPeek フロントエンド                    │
│    💬 チャット  │  👤 プロフィール  │  🔗 ナレッジグラフ  │  ✨ 特徴  │
└──────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌──────────────────────────────────────────────────────────────────┐
│                     🤖 LangGraph オーケストレーター                  │
│  ┌────────────┐  ┌────────────┐  ┌────────────┐  ┌───────────┐ │
│  │  Feature   │  │  Latent    │  │Relationship│  │ DeepThink │ │
│  │ Discovery  │  │   Intent   │  │  Agent     │  │   Agent   │ │
│  └────────────┘  └────────────┘  └────────────┘  └───────────┘ │
└──────────────────────────────────────────────────────────────────┘
                                │
        ┌───────────────────────┼───────────────────────┐
        ▼                       ▼                       ▼
┌───────────────┐    ┌───────────────┐    ┌───────────────┐
│   💾 SQLite   │    │  📡 MemoBase │    │  🧠 LLM       │
│   ローカル    │    │   リモート   │    │  (DeepSeek等)  │
└───────────────┘    └───────────────┘    └───────────────┘
```

## 🛠️ 技術スタック

### バックエンド
- **FastAPI** - 高性能非同期Webフレームワーク
- **LangGraph** - マルチAgentオーケストレーションツール
- **SQLAlchemy** - 非同期ORM
- **NetworkX** - ナレッジグラフ
- **Pydantic** - データ検証

### フロントエンド
- **Vue 3** - コンポジションAPI
- **Element Plus** - UIコンポーネントライブラリ
- **Pinia** - 状態管理
- **ECharts** - データ可視化
- **vis-network** - ナレッジグラフ可視化

### AI機能
- **OpenAI互換インターフェース** - すべての主要なLLMをサポート
- **DeepSeek** - デフォルト設定
- **通義千問 / 智譜AI / Ollama** - すべてサポート

## 🚀 クイックスタート

### 1. 依存関係のインストール

```bash
cd MindPeek
pip install -r requirements.txt
cd frontend && npm install
```

### 2. システム設定

```bash
copy config\config.example.json config\config.json
```

`config/config.json`を編集して設定を入力：

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
        "comment": "並行Agentの最大数を制御、サーバーパフォーマンスに応じて調整、推奨値1-5"
    }
}
```

### 3. サービスの起動

```bash
# バックエンド (ターミナル 1)
cd MindPeek
python -m uvicorn main:app --host 0.0.0.0 --port 8000

# フロントエンド (ターミナル 2)
cd MindPeek/frontend
npm run dev
```

### 4. 開始

- 🌐 フロントエンド：http://localhost:3000
- 📖 APIドキュメント：http://localhost:8000/docs

## 📁 プロジェクト構造

```
MindPeek/
├── main.py                     # FastAPI エントリーポイント
├── requirements.txt            # Python 依存関係
├── config/
│   ├── config.json             # ランタイム設定
│   └── config.example.json    # 設定テンプレート
├── backend/
│   ├── api/
│   │   └── routes.py          # APIルート
│   ├── models/
│   │   ├── database.py         # データベースモデル
│   │   └── schemas.py         # Pydanticモデル
│   ├── services/
│   │   ├── llm_provider.py    # マルチプロバイダーサポート
│   │   ├── profile_service.py # ユーザープロフィリングサービス
│   │   └── memo_base_service.py # リモートストレージ
│   ├── agents/
│   │   ├── chat_graph.py      # 🤖 LangGraphチャットグラフ
│   │   ├── feature_discovery.py # 🔮 特徴発見Agent
│   │   ├── async_orchestrator.py # ⚡ 非同期タスクオーケストレーション
│   │   └── agent_engine.py    # Agentエンジン
│   └── knowledge_graph/
│       └── graph.py           # 🔗 ナレッジグラフ
├── frontend/
│   ├── src/
│   │   ├── views/             # ページコンポーネント
│   │   ├── stores/            # Pinia状態
│   │   ├── api/               # API呼び出し
│   │   └── router/            # ルーター設定
│   └── package.json
└── data/
    └── permir.db              # SQLiteデータベース
```

## 🎨 機能

### 💬 インテリジェントチャット
- 自動コンテキスト理解による多対話
- あなたのプロファイルに合わせたパーソナライズされた応答
- オプションの深層思考モード

### 👤 ユーザープロファイル
- MBTI性格分析
- Big Fiveパーソナリティーレーダーチャート
- 行動習慣の洞察
- 隠れたニーズの発見

### 🔗 ナレッジグラフ
- 特徴相関の可視化
- ソーシャルリレーションシップネットワーク
- 動的に更新されるグラフ

### 🔮 Agentダッシュボード
- リアルタイムAgentタスクステータス
- 非同期タスク管理
- インサイトレポート

## 📜 ライセンス

GNU General Public License v3.0 (GPL-3.0)

詳細は[LICENSE](LICENSE)を参照してください。

---

<p align="center">
  <strong>MindPeek</strong> - AIにあなたを真に理解させる
</p>
