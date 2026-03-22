# MindPeek - あなたのことを理解するAIパートナー 🎯

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.9+-blue.svg" alt="Python">
  <img src="https://img.shields.io/badge/Vue-3-green.svg" alt="Vue">
  <img src="https://img.shields.io/badge/License-GPL--3.0-orange.svg" alt="License">
  <img src="https://img.shields.io/badge/LangGraph-Enabled-purple.svg" alt="LangGraph">
</p>

> *MindPeekは普通のチャットボットではありません —— あなたを真に理解するAIパートナーです。マルチターン対話と先進的なAI Agent技術を通じて、MindPeekはあなたをますます理解し、かけがえのないIntelligentアシスタントになります。*

---

**🌐 Language**: [English](README_en.md) | [中文](README.md) | [日本語](README_ja.md)

---

## ✨ コア機能

MindPeekはあなたの対話を深い理解に変換します：

| 🔮 Agent | 💡 機能 | 🎯 価値 |
|---------|--------|---------|
| **FeatureDiscovery Agent** | 性格、習慣、偏好を自動的に発見 | 手動入力不要、AIが自動学習 |
| **LatentIntent Agent** | 隠れたニーズと潜在的な意図を識別 | あなたが]~!b[る前にあなたのニーズを知る |
| **CorrelationAgent** | 特徴間の相関を発見 | 完全なユーザープロファイルネットワークを構築 |
| **DeepThink Agent** | 深い心理分析 | 言動の背後にある心理的動機を探る |

## 🚀 なぜMindPeekを選ぶのか？

### 🤖 マルチAgent協調システム
LangGraph上に構築されたIntelligent Agentネットワーク、複数の専門Agentが協調して動作：
- **非同期処理**：スムーズな対話、バックグラウンドタスクが自動実行
- **スマートルーティング**：パーソナライズと汎用返信の切り替えを自動判断
- **並列分析**：特徴抽出、相関分析、ニーズ発見が同時に実行

### 🧠 自分より自分をよく理解
- **能動的学習**：対話を通じてMBTI、行動習慣、兴趣爱好を自動発見
- **隠れたニーズ発掘**：言っていないが実際必要なものを発見
- **ダイナミックなプロファイリング**：対話が深まるほどプロファイルが精密に

### 🔄 インテリジェント特徴減衰メカニズム
- **LLM評価安定性**：各特徴の安定性を大モデルが判断
- **パーソナライズされた減衰曲線**：安定特徴は緩やかに減衰、変動特徴は速く減衰
- **遅延更新戦略**：ユーザーのアクセス時のみ減衰を計算、データベース書き込みを削減
- **対数減衰関数**：
  - 安定期間中は完全不減衰
  - 安定期間後は緩やかな対数減衰を開始
  - 最終的に最小閾値（0.3）に収束

```
C(t) = C₀ - 0.3 × (C₀ - 0.3) × ln(1 + (t - T_stable) × r)
```

### 🔗 社会的関係認識
- 対話の中で言及された人物を自動識別（家族、友人、同僚など）
- あなたの対人的相互作用パターンを理解
- 完全な社会的関係マップを構築

### ⚡ 本番環境グレードのパフォーマンス
- 最大3つのAgentが並列実行する非同期タスクキュー
- ゼロレイテンシーのユーザー対話体験
- 自動バックグラウンドタスクスケジューリング

### 💾 デュアルストレージアーキテクチャ
- **SQLiteローカルストレージ**：コアユーザーデータ、対話履歴、特色情報
- **MemoBaseリモート同期**：クロスデバイス特徴同期、クラウドバックアップ

## 📊 システムアーキテクチャ

```
┌──────────────────────────────────────────────────────────────────┐
│                         MindPeek フロントエンド                    │
│    💬 チャット  │  👤 プロフィール  │  🔗 ナレッジグラフ  │  ✨ 特徴  │  ⚙️ 設定   │
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
│   ローカル    │    │   リモート    │    │  (DeepSeek等)  │
└───────────────┘    └───────────────┘    └───────────────┘
                                │
                                ▼
                    ┌───────────────────────┐
                    │  🧠 ナレッジグラフ    │
                    │  事前定義心理学知識   │
                    │  ベース + リアルタイ  │
                    │  ム推論エンジン       │
                    └───────────────────────┘
```

## 🛠️ 技術スタック

### バックエンド
- **FastAPI** - 高性能非同期Webフレームワーク
- **LangGraph** - マルチAgentオーケストレーションツール
- **SQLAlchemy** - 非同期ORM
- **ナレッジグラフ** - 事前定義心理学知識ベース + リアルタイム推論
- **Pydantic** - データ検証

### フロントエンド
- **Vue 3** - コンポジションAPI
- **Element Plus** - UIコンポーネントライブラリ
- **Pinia** - 状態管理
- **ECharts** - データ可視化
- **vis-network** - ナレッジグラフ可視化

### AI機能
- **OpenAI互換インターフェース** - すべての主流大モデルをサポート
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
        "comment": "最大並列Agent数、サーバー性能に応じて調整、推奨値1-5"
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

### 4. 探索を開始

- 🌐 フロントエンド：http://localhost:3000
- 📖 APIドキュメント：http://localhost:8000/docs

## 📁 プロジェクト構造

```
MindPeek/
├── main.py                     # FastAPIエントリーポイント
├── requirements.txt            # Python依存関係
├── config/
│   ├── config.json             # ランタイム設定
│   └── config.example.json     # 設定テンプレート
├── backend/
│   ├── api/
│   │   └── routes.py           # APIルート
│   ├── models/
│   │   ├── database.py         # データベースモデル
│   │   └── schemas.py          # Pydanticモデル
│   ├── services/
│   │   ├── llm_provider.py     # マルチプロバイダーサポート
│   │   ├── profile_service.py  # ユーザープロファイルサービス
│   │   └── memo_base_service.py # リモートストレージ
│   ├── agents/
│   │   ├── chat_graph.py       # 🤖 LangGraphチャットグラフ
│   │   ├── feature_discovery.py # 🔮 特徴発見Agent
│   │   ├── async_orchestrator.py # ⚡ 非同期タスクオーケストレーション
│   │   └── agent_engine.py     # Agentエンジン
│   └── knowledge_graph/
│       └── graph.py           # 🔗 ナレッジグラフ（リアルタイム推論）
├── frontend/
│   ├── src/
│   │   ├── views/             # ページコンポーネント
│   │   ├── stores/            # Pinia状態
│   │   ├── api/               # API呼び出し
│   │   └── router/            # ルート設定
│   └── package.json
└── data/
    └── permir.db              # SQLiteデータベース
```

## 🎨 機能紹介

### 💬 インテリジェントチャット
- マルチターン対話、自動コンテキスト理解
- 特色に基づいたパーソナライズ返信
- ディープシンキングモードオプション

### 👤 ユーザープロファイル
- MBTI性格分析
- Big Fiveパーソナリティーレーダーチャート
- 行動習慣洞察
- 隠れたニーズ発見

### 🔗 ナレッジグラフ
- 事前定義心理学知識ベースに基づくリアルタイム推論
- 特徴相関可視化
- 潜在特徴の動的推論

### 🔮 Agentワークベンチ
- Agentタスクステータスのリアルタイム表示
- 非同期タスク管理
- インサイトレポート

## 📜 License

GNU General Public License v3.0 (GPL-3.0)

[LICENSE](LICENSE)をご確認ください。

---

<p align="center">
  <strong>MindPeek</strong> - AIにあなたを真に理解させる
</p>
