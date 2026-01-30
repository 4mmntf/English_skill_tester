# 英会話能力測定AIアプリ 仕様書

## プロジェクト概要

英会話能力を測定するためのAIアプリケーション。OpenAI Realtime API、GPT-5シリーズ、Azure Pronunciation Assessmentを活用して、リアルタイムで英会話能力を評価する。

## 技術スタック

### アプリケーション
- **開発環境**: macOS
- **配布プラットフォーム**: Windows
- **言語**: Python 3.14
- **GUIフレームワーク**: Flet（FlutterベースのクロスプラットフォームGUI）
- **アーキテクチャ**: デスクトップアプリケーション（Webサーバー不要）
- **パッケージング**: PyInstaller（Windows実行ファイルとして配布可能）
- **プラットフォーム**: macOS（開発）、Windows（配布）

### 利用API
- **開発中**: 
  - OpenAI Realtime API
  - GPT-5 nano
  - Azure Pronunciation Assessment
- **本番環境**:
  - OpenAI Realtime API
  - GPT-5 nano / GPT-5 mini / GPT-5.2
  - Azure Pronunciation Assessment

### 外部通信
- **LLM API**: OpenAI Realtime API、GPT-5シリーズとの通信
- **データ保存**: ローカルファイルへの保存（ユーザー認証不要）
- **その他**: Webサーバーは使用しない、ユーザー認証は行わない

## 機能要件

### 画面構成（段階的開発）
1. **ホーム画面** - アプリの説明と開始ボタン
2. **会話画面** - リアルタイム音声対話と評価表示
3. **結果画面** - 評価結果の詳細表示
4. **履歴画面** - 過去の評価履歴一覧

### 主要機能
- リアルタイム音声対話
- 発音評価（Azure Pronunciation Assessment）
- 会話内容の理解度評価（GPT-5）
- 総合的な英会話能力スコア算出
- 評価履歴の保存・閲覧

## プロジェクト構造

```
english_skill3/
├── app/
│   ├── __init__.py
│   ├── main.py
│   ├── gui/
│   │   ├── __init__.py
│   │   ├── home_window.py
│   │   ├── conversation_window.py
│   │   ├── result_window.py
│   │   └── history_window.py
│   ├── services/
│   │   ├── __init__.py
│   │   ├── openai_service.py
│   │   ├── azure_service.py
│   │   ├── evaluation_service.py
│   │   └── storage_service.py
│   └── models/
│       ├── __init__.py
│       └── schemas.py
├── pyproject.toml
├── uv.lock
├── .env.example
├── README.md
└── specifications.md
```

## 開発方針

- 1画面ずつ機能を追加
- 都度ユーザーによるチェックを実施
- API利用料削減のため、開発中はGPT-5 nanoを使用
- 段階的な機能実装とテスト
- macOSで開発、Windows実行ファイルとして配布可能な形式で開発

## パッケージ管理

このプロジェクトはuvを使用してパッケージを管理します。

### 依存関係のインストール

```bash
uv sync
```

### 依存関係の追加

```bash
uv add <package-name>
```

## ビルドと配布

### Windows実行ファイルの作成

PyInstallerを使用してWindows実行ファイル（.exe）を作成します：

```bash
# uvを使用して実行
uv run pyinstaller --onefile --windowed --name "EnglishSkillApp" app/main.py

# または、build_windows.specを使用
uv run pyinstaller build_windows.spec
```

### 配布形式

- 単一実行ファイル（.exe）として配布
- インストーラー形式（オプション）

## 環境変数

- `OPENAI_API_KEY`: OpenAI APIキー
- `AZURE_SPEECH_KEY`: Azure Speech Serviceキー
- `AZURE_SPEECH_REGION`: Azure Speech Serviceリージョン

## データ保存

- 評価データはローカルファイルに保存されます
  - Windows: `AppData\Local\EnglishSkillApp\evaluations\`
  - macOS: `~/Library/Application Support/EnglishSkillApp/evaluations/`
- ユーザー認証は不要です
- データはJSON形式で保存されます

