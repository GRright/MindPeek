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

## 🖼️ デモギャラリー

<p align="center">
  <table>
    <tr>
      <td align="center">
        <img src="docs/images/page/chat.png" width="300" alt="チャット画面"/>
        <br/>
        <strong>チャット画面</strong>
      </td>
      <td align="center">
        <img src="docs/images/page/chat1.png" width="300" alt="スマートシンキング"/>
        <br/>
        <strong>スマートシンキング</strong>
      </td>
      <td align="center">
        <img src="docs/images/page/feature1.png" width="300" alt="特徴管理"/>
        <br/>
        <strong>特徴管理</strong>
      </td>
    </tr>
    <tr>
      <td align="center">
        <img src="docs/images/page/knowledge-graph.png" width="300" alt="特徴グラフ"/>
        <br/>
        <strong>特徴グラフ</strong>
      </td>
      <td align="center">
        <img src="docs/images/page/profile1.png" width="300" alt="ユーザープロファイル1"/>
        <br/>
        <strong>ユーザープロファイル</strong>
      </td>
      <td align="center">
        <img src="docs/images/page/profile2.png" width="300" alt="ユーザープロファイル2"/>
        <br/>
        <strong>特徴分布</strong>
      </td>
    </tr>
  </table>
</p>

---

## 🚀 クイックスタート

### 1. 依存関係のインストール

```bash
pip install -r requirements.txt
cd frontend
npm install
```

### 2. システム設定

```bash
copy config\config.example.json config\config.json
```

`config/config.json`を編集して、LLM API設定を入力してください。

### 3. サービスの起動

```bash
python -m uvicorn main:app --host 0.0.0.0 --port 8000
cd frontend
npm run dev
```

### 4. 始めましょう

- 🌐 フロントエンド：http://localhost:3000
- 📖 APIドキュメント：http://localhost:8000/docs

### 5. クイックテスト（推奨）

インタラクティブテストスクリプトを実行して、すべての機能を素早く体験：

```bash
python tests/interactive_conversation_test.py
```

このスクリプトは自動的に：
- 30ラウンドのシミュレートされた会話を送信
- ユーザー特徴を抽出（MBTI、興味、価値観など）
- ユーザープロファイルとナレッジグラフを生成
- スマートアラートとプロファイルトレンド分析をトリガー

テスト後、以下のページで結果を確認：
- 📊 特徴管理：http://localhost:3000/features
- 🔗 ナレッジグラフ：http://localhost:3000/knowledge-graph

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

## ⚡ システム機能

### 🧠 インテリジェントユーザープロファイリング
- **ディープ会話解析**：継続的な対話を通じてユーザー特徴を自動抽出
- **多次元プロファイリング**：性格、興味、価値観、感情状態などをカバー
- **継続的進化**：ユーザープロファイルは会話と共に常に更新・改善

### 🔄 タブ間会話履歴同期
- **データベース永続化**：すべての会話が自動保存、失われない
- **タブ間同期**：新しいタブで即座に完全な会話履歴を表示
- **思考内容保存**：AIの深い思考プロセスも記録

### 🎨 レスポンシブUIデザイン
- **デスクトップ**：左右分割レイアウトで完全な機能表示
- **モバイル**：アダプティブ最適化、コア機能優先
- **ヒューマナイズドインタラクション**：スマートスクロール、ユーザーの読書を中断しない

### 🔔 スマート感情アラート
- **リアルタイム感情モニタリング**：ネガティブな感情状態を自動識別
- **タイムリーな健康警告**：異常が検出された際に積極的にアラート
- **パーソナライズされた提案**：ユーザーの状況に基づいたケア

### 🔗 ビジュアル特徴グラフ
- **ナレッジグラフ表示**：特徴間の関係を直感的に表現
- **特徴分布チャート**：ユーザープロファイルの構成を可視化
- **インタラクティブ探索**：クリックして詳細な特徴情報を表示

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
