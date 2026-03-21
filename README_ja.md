# MindPeek - インテリジェントユーザーuproファイル生成システム

LLMを使用したマルチターン対話型ユーザーuproファイル生成システム。MindPeekは自然な対話を通じて、MBTI性格タイプ、大五人格特性、行動習慣、潜在的な思考など、ユーザーの暗黙的な特性を深く分析し、ユーザー研究とパーソナライズされたサービスをサポートします。

---

**🌐 Language / 语言 / 言語**: [English](README_en.md) | [中文](README.md) | [日本語](README_ja.md)

---

## 主な機能

- **インテリジェントな特徴抽出**：マルチターン対話からMBTI性格タイプ、大五人格特性、行動習慣、潜在的な思考などを自動的に識別
- **リアルタイムuproファイル更新**：対話が深まるにつれて、システムが継続的に学習し、ユーザーuproファイルを更新
- **ナレッジグラフ可視化**：ユーザー特性間の関係をグラフ形式で表示
- **マルチバックエンドストレージサポート**：SQLiteローカルストレージとMemoBaseリモートストレージをサポート
- **OpenAI互換インターフェース**：OpenAI互換APIを提供するLLMサービスに接続可能
- **モダンブ론エンドインターフェース**：Open WebUIにインスパイアされたダークテーマインターフェース

## 技術スタック

### バックエンド

- **FastAPI** - 高速Python Webフレームワーク
- **SQLAlchemy** - 非同期ORMデータベースアクセス
- **httpx** - 非同期HTTPクライアント
- **Pydantic** - データ検証とモデル定義
- **NetworkX** - ナレッジグラフ構築

### フロントエンド

- **Vue 3** - プログレッシブJavaScriptフレームワーク
- **Element Plus** - UIコンポーネントライブラリ
- **Pinia** - 状態管理
- **vis-network** - ナレッジグラフ可視化
- **ECharts** - データ可視化チャート

### サポートされているLLM

このシステムはOpenAI互換インターフェースを通じてLLMに接続します：

- DeepSeek（デフォルト設定）
- 通義千問
- 智譜AI
- Ollama（ローカルモデル）
- OpenAI GPTシリーズ
- OpenAI互換APIを提供する任意の serviço

## 環境要件

- Python 3.9+
- Node.js 18+
- インターネット接続（LLM呼び出しに必要）

## クイックスタート

### 1. 依存関係のインストール

```bash
cd MindPeek
pip install -r requirements.txt
cd frontend
npm install
cd ..
```

### 2. システム設定

> :warning: **重要**: `config.example.json`をコピーして`config.json`に名前を変更し你自己的設定情報を入力してください。

設定ファイルテンプレートをコピーして編集：

```bash
copy config\config.example.json config\config.json
```

`config/config.json`を編集し、LLMとMemoBaseの情報を入力：

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

**設定の説明:**
- `api_key`: APIキー（ローカルLLMデプロイでは`dummy_key`などの任意の文字列を使用可能）
- `api_url`: LLM/MemoBaseサービスのアドレス
- `model`: 使用するモデル名

### 3. サービスの起動

バックエンドを起動（ターミナル1）：

```bash
cd MindPeek
python -m uvicorn main:app --host 0.0.0.0 --port 8000
```

フロントエンドを起動（ターミナル2）：

```bash
cd MindPeek/frontend
npm run dev
```

### 4. システムへのアクセス

- フロントエンドUI: http://localhost:3000
- APIドキュメント: http://localhost:8000/docs
- ヘルスチェック: http://localhost:8000/health

## 設定の詳細

### LLMプロバイダー設定

| パラメータ | 説明 | 例 |
|-----------|------|-----|
| `enabled` | このプロバイダーを有効にするか | `true` |
| `api_key` | APIキー（ローカルデプロイではdummy_keyを使用可能） | `dummy_key` |
| `api_url` | APIアドレス（OpenAI互換形式） | `http://172.16.5.147:8000/v1` |
| `model` | モデル名 | `deepseek-chat` |
| `temperature` | 生成温度（0-1） | `0.7` |
| `max_tokens` | 最大トークン数 | `2000` |

### MemoBase設定

MemoBaseはユーザーuproファイルと対話履歴の遠隔ストレージとして使用されます：

| パラメータ | 説明 | 例 |
|-----------|------|-----|
| `enabled` | MemoBaseを有効にするか | `true` |
| `project_url` | MemoBaseサービスアドレス | `http://172.16.5.147:8019` |
| `api_key` | MemoBase APIキー | `GdyztMemobase2025` |

## 機能モジュール

### チャット分析

チャットインターフェースでAIと自然な対話をします。システムは対話内容をリアルタイムで分析し、ユーザー特性を抽出します。

### ユーザーuproファイル

グラフ形式のユーザーuproファイルを参照：
- MBTI性格四象限分析
- 特性レーダーチャート
- 信頼度表示

### ナレッジグラフ

特性間の関係をノードとエッジの形式で表示し、ユーザー特性の内部联系を理解するのに役立ちます。

### 特性管理

抽出されたユーザー特性を参照、フィルタリング、管理します。

## プロジェクト構造

```
MindPeek/
├── main.py                     # FastAPIアプリケーションエントリ
├── requirements.txt            # Python依存関係
├── config/
│   ├── config.json             # 実行時設定ファイル
│   └── config.example.json    # 設定テンプレート
├── backend/
│   ├── api/
│   │   └── routes.py          # APIルート定義
│   ├── core/
│   │   └── config.py          # 設定管理モジュール
│   ├── models/
│   │   ├── database.py         # SQLAlchemyモデル
│   │   └── schemas.py         # Pydanticモデル
│   ├── services/
│   │   ├── llm_provider.py    # LLMプロバイダー（マルチプロバイダーサポート）
│   │   ├── profile_service.py  # ユーザーuproファイルサービス
│   │   └── memo_base_service.py # MemoBaseストレージサービス
│   ├── agents/
│   │   └── agent_engine.py    # マルチエージェント協調エンジン
│   └── knowledge_graph/
│       └── graph.py           # ナレッジグラフモジュール
├── frontend/                   # Vue 3 フロントエンド
│   ├── src/
│   │   ├── views/             # ページコンポーネント
│   │   ├── stores/            # Pinia状態管理
│   │   ├── api/               # API呼び出しラッパー
│   │   └── router/            # Vue Router設定
│   └── package.json
└── data/                       # データストレージディレクトリ
    └── permir.db              # SQLiteデータベース
```

## ライセンス

GNU General Public License v3.0 (GPL-3.0)

詳細については[LICENSE](LICENSE)を参照してください。
