# MindPeek - あなたを理解するAIパートナー 🎯

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.9+-blue.svg" alt="Python">
  <img src="https://img.shields.io/badge/Vue-3-green.svg" alt="Vue">
  <img src="https://img.shields.io/badge/License-GPL--3.0-orange.svg" alt="License">
  <img src="https://img.shields.io/badge/LangGraph-Enabled-purple.svg" alt="LangGraph">
</p>

<p align="center">
  <strong>AIが本当にあなたを理解する</strong>
</p>

<p align="center">
  <a href="README_en.md">English</a> | <a href="README.md">中文</a> | <a href="README_ja.md">日本語</a>
</p>

---

## ✨ 主な機能

### 🧠 インテリジェントユーザープロファイリング

MindPeekはLLMを活用して会話を解析し、継続的に進化するユーザープロファイルを構築します：

| 次元 | 説明 |
|------|------|
| **性格** | MBTI、ビッグファイブ分析 |
| **行動** | 習慣、意思決定パターン |
| **興味** | エンターテイメント、学習の好み |
| **価値観** | 人生観、世界観 |
| **感情** | 現在の気分、心理的ニーズ |
| **関係性** | ソーシャルネットワーク、交流パターン |

### 🔮 AI行動予測

ユーザープロファイルに基づいて、将来の行動や思考を予測：
- **行動予測**：ユーザーがとる可能性のある行動
- **思考予測**：ユーザーが持つ可能性のあるアイデア
- **感情予測**：ユーザーが経験する可能性のある感情状態
- **意思決定予測**：ユーザーが下す可能性のある選択

### 💬 パーソナライズされた会話

AIはあなたのプロファイルに基づいて思いやりのある応答を提供：
- あなたの興味や習慣を自然に取り入れる
- あなたの性格に合わせてトーンを調整
- あなたのニーズを先読みして提案
- 古い友人のように自然に会話

---

## 🚀 クイックスタート

### 1. 依存関係のインストール

```bash
pip install -r requirements.txt
cd frontend && npm install
```

### 2. システム設定

```bash
copy config\config.example.json config\config.json
```

`config/config.json`を編集して、LLM API設定を入力してください。

### 3. サービスの起動

```bash
python -m uvicorn main:app --host 0.0.0.0 --port 8000
cd frontend && npm run dev
```

### 4. 始めましょう

- 🌐 フロントエンド：http://localhost:3000
- 📖 APIドキュメント：http://localhost:8000/docs

---

## 📊 システムアーキテクチャ

```
┌─────────────────────────────────────────────────────────────────┐
│                        MindPeek フロントエンド                     │
│   💬 チャット  │  👤 プロファイル  │  🔗 ナレッジグラフ  │  ✨ 特徴  │  ⚙️ 設定   │
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
│    💾 SQLite   │  │   📡 MemoBase  │  │       🧠 LLM        │
│   ローカル保存  │  │   リモート同期  │  │   (DeepSeek等)      │
└─────────────────┘  └─────────────────┘  └─────────────────────┘
```

---

## 🛠️ 技術スタック

| レイヤー | 技術 |
|----------|------|
| **バックエンド** | FastAPI + LangGraph + SQLAlchemy |
| **フロントエンド** | Vue 3 + Element Plus + ECharts |
| **AI** | OpenAI互換API + Sentence Transformers |
| **ストレージ** | SQLite + MemoBaseクラウド同期 |

---

## 🆕 最新機能

### スマートインテント分類
**Embeddingセマンティック理解**に基づくインテリジェントなインテント分類：
- ハイブリッドアプローチ：ルール優先 + Embeddingセマンティック判断
- 高パフォーマンス：90%以上のリクエストがミリ秒で応答
- スマート理解：同義語やバリアントの正確な認識

### 特徴減衰メカニズム
![減衰関数図](docs/images/decay_function_en.png)

- **安定期間**：特徴の信頼度は変化しない
- **減衰期間**：対数減衰、最終的に最小閾値に収束
- **レイジーアップデート**：アクセス時に計算、データベース書き込みを削減

---

## 📁 プロジェクト構造

```
MindPeek/
├── backend/
│   ├── agents/          # エージェントモジュール
│   │   ├── chat_graph.py          # 会話フロー
│   │   ├── feature_discovery.py   # 特徴発見
│   │   ├── prediction_agent.py    # 行動予測
│   │   └── intent_classifier.py   # インテント分類
│   ├── services/        # サービス層
│   ├── knowledge_graph/ # ナレッジグラフ
│   └── models/          # データモデル
├── frontend/            # Vue 3 フロントエンド
└── config/              # 設定ファイル
```

---

## 📜 ライセンス

[GNU General Public License v3.0](LICENSE)

---

<p align="center">
  <strong>MindPeek</strong> - AIに本当に理解させる
</p>
