# 英会話能力測定AIアプリ

> This project was created by the AI code editor "Cursor".
> The large language model (LLM) used by Cursor is "GPT-4.1".
> Detailed specifications are documented in [specifications.md](.cursor_memo/specifications.md).

## 概要

英会話能力を測定するためのデスクトップアプリケーションです。OpenAI Realtime API、GPT-5シリーズを活用して、リアルタイムで英会話能力を評価します。

### 主な機能

- **リアルタイム英会話**: OpenAI Realtime APIを使用したAI講師とのリアルタイム音声対話
- **複数のテスト項目**: 会話テスト、リスニングテスト（予定）
- **自動評価機能**: 会話内容を自動的に分析し、文法・語彙・表現・流暢さを評価
- **ロールプレイ機能**: レストラン、ホテル、空港など様々なシーンでの会話練習
- **音声デバイステスト**: マイク・スピーカーの動作確認とリアルタイム波形表示
- **API状態確認**: OpenAI APIの接続状態を確認
- **データ自動保存**: 評価データはローカルファイルに自動保存（ユーザー認証不要）

## 技術スタック

- **開発環境**: macOS / Windows
- **配布プラットフォーム**: Windows（PyInstallerで実行ファイル化）
- **言語**: Python 3.14.2
- **GUIフレームワーク**: Flet（FlutterベースのクロスプラットフォームGUI）
- **パッケージング**: PyInstaller（Windows実行ファイルとして配布可能）
- **API**: OpenAI Realtime API, GPT-5
- **データ保存**: ローカルファイル（ユーザー認証不要）

## セットアップ

### 必要な環境

- Python 3.14（Tkinterサポート付き）
- uv（Pythonパッケージマネージャー）

### 注意事項

**macOS開発環境**: このプロジェクトはmacOSで開発されています。Fletはクロスプラットフォーム対応のため、macOSでも問題なく開発・テストできます。

**Windows配布**: 最終的な配布はWindows実行ファイル（.exe）として行いますが、開発・テストはmacOSで行います。

### uvのインストール

uvがインストールされていない場合：

```bash
# macOS/Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# Windows
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

### インストール手順

1. リポジトリをクローンします
2. 依存パッケージをインストールします：
```bash
uv sync
```

3. 環境変数を設定します：
プロジェクトルートに`.env`ファイルを作成し、必要なAPIキーを設定してください。

**必要な環境変数**：
- `OPENAI_API_KEY` または `OPENAI_API`: OpenAI APIキー（Realtime APIと評価機能で使用）
- `OPENROUTER_API_KEY`: OpenRouter APIキー（リスニングテストで使用）

`.env`ファイルの例：
```env
OPENAI_API_KEY=your_openai_api_key_here
OPENROUTER_API_KEY=your_openrouter_api_key_here
```

**注意**: `OPENAI_API_KEY`は必須です。

### 実行方法

#### 開発環境での実行

```bash
# uvを使用して実行
uv run python app/main.py

# または、uv sync後に直接実行
python app/main.py
```

#### Windows実行ファイルのビルド

```bash
# uvを使用してPyInstallerを実行
uv run pyinstaller build_windows.spec

# または、ビルドスクリプトを実行（Windows）
build.bat
```

ビルド後、`dist/EnglishSkillApp.exe`が生成されます。

詳細は [specifications.md](.cursor_memo/specifications.md) を参照してください。

### テストの実行

プロジェクトには包括的なテストスイートが含まれています。

```bash
# すべてのテストを実行
uv run pytest

# カバレッジレポート付きでテストを実行
uv run pytest --cov=app --cov-report=html

# 特定のテストファイルを実行
uv run pytest tests/test_imports.py

# テストスクリプトを使用（推奨）
./run_tests.sh
```

テスト実行時は、環境変数が設定されていない場合に備えて、ダミーの環境変数が自動的に設定されます。

## トラブルシューティング

問題が発生した場合は、[TROUBLESHOOTING.md](.cursor_memo/TROUBLESHOOTING.md)を参照してください。

## 使用方法

アプリケーションを起動すると、タブベースのメイン画面が表示されます。各タブで異なるテスト項目を実行できます。

### 画面構成

アプリケーションは以下のタブで構成されています：

1. **メイン画面タブ**
   - API接続状態の確認（OpenAI API）
   - マイク・スピーカーのテスト機能
   - リアルタイム音声波形の表示
   - テストデータの初期化機能

2. **会話テストタブ**（実装済み）
   - リアルタイム英会話の評価機能（詳細は後述）
   - OpenAI Realtime APIを使用したリアルタイム音声対話
   - ロールプレイ機能
   - 自動評価機能

3. **リスニングテストタブ**（開発中）
   - 聞き取り能力を評価します
   - 音声を聞いて理解度を測定する機能を予定

### メイン画面タブの使い方

1. **API状態の確認**
   - アプリ起動時に自動的にAPI接続状態をチェックします
   - 各APIの状態が色分けで表示されます（緑：利用可能、オレンジ：警告、赤：エラー）

2. **マイク・スピーカーのテスト**
   - 「Hello」と発話してマイク・スピーカーをテスト」ボタンをクリック
   - 3秒間録音後、自動的に再生されます
   - 録音・再生の波形がリアルタイムで表示されます

3. **リアルタイム波形表示**
   - マイクの音声入力がリアルタイムで波形として表示されます
   - 音声入力の強度を視覚的に確認できます

### 会話テストタブの使い方

会話テストでは、OpenAI Realtime APIを使用してAI講師とリアルタイムで英会話を行い、会話能力を評価します。

#### 基本的な使い方

1. **ロールプレイシーンの選択**
   - ドロップダウンから会話シーンを選択します（例：レストラン、ホテル、空港など）
   - 選択したシーンに応じてAI講師の役割が設定されます

2. **テストの開始**
   - 「テストを開始する」ボタンをクリックして会話を開始します
   - AI講師が最初に話しかけてきます

3. **リアルタイム会話**
   - マイクに向かって話すと、音声が自動的に認識され、AI講師に送信されます
   - AI講師の音声が自動的に再生されます
   - 会話履歴が画面に表示されます

4. **テストの制御**
   - 「テストを一時停止する」ボタンで会話を一時停止できます
   - 「テストを中断する」ボタンで会話を終了できます
   - 右上に全体の経過時間が表示されます

#### 評価機能

会話テストでは、リアルタイムで会話内容を評価する機能が実装されています。

**評価の仕組み**

1. **会話履歴の記録**
   - AI講師と学生の発話を自動的に記録します
   - 発話は「AI講師: ...」「学生: ...」の形式で保存されます

2. **評価の実行タイミング**
   - **会話セッション中**: AIと学生が2往復以上（4発話以上）した時点で自動的に評価を実行します
   - **会話セッション終了後**: テスト中断時または正常終了時に最終評価を実行します

3. **評価方法**
   - OpenAI API（GPT-5）を使用して会話内容を評価します
   - 以下の観点で評価を行います：
     - 会話として成立しているか（お互いの意図が伝わっているか、適切な応答ができているか）
     - 文法の正確性（0-100点）
     - 語彙の適切性（0-100点）
     - 表現の自然さ（0-100点）
     - 会話の流暢さ（0-100点）
   - 評価結果はJSON形式で返され、総合スコア（0-100点）とフィードバックコメントが生成されます

4. **評価結果の表示**
   - 評価結果は会話テストタブのステータステキストに表示されます
   - 会話が成立している場合は緑色、不成立の場合はオレンジ色で表示されます
   - 総合スコアとフィードバックコメントが表示されます

**評価プロンプトの詳細**

評価は以下のプロンプトを使用してGPT-5に依頼します：

```
以下の英会話を評価してください。以下の観点で評価をお願いします：
1. 会話として成立しているか（お互いの意図が伝わっているか、適切な応答ができているか）
2. 文法の正確性
3. 語彙の適切性
4. 表現の自然さ
5. 会話の流暢さ

評価結果を以下のJSON形式で返してください：
{
    "is_valid": true/false,  // 会話として成立しているか
    "grammar_score": 0-100,  // 文法の正確性スコア
    "vocabulary_score": 0-100,  // 語彙の適切性スコア
    "naturalness_score": 0-100,  // 表現の自然さスコア
    "fluency_score": 0-100,  // 会話の流暢さスコア
    "overall_score": 0-100,  // 総合スコア
    "feedback": "評価コメント"
}
```

評価はバックグラウンドスレッドで実行されるため、会話の進行を妨げません。

### データの保存

- 評価データは自動的にローカルファイルに保存されます
- 保存先：
  - Windows: `AppData\Local\EnglishSkillApp\evaluations\`
  - macOS: `~/Library/Application Support/EnglishSkillApp/evaluations/`
- データはJSON形式で保存され、ユーザー認証は不要です

### テストの初期化

メイン画面タブの「テストを初めから実行するために，データを初期化する」ボタンをクリックすると、すべてのテストデータがリセットされ、最初からテストを実行できます。

## プロジェクト構造

```
english_skill3/
├── app/
│   ├── __init__.py
│   ├── main.py                 # アプリケーションのエントリーポイント
│   ├── config.py              # アプリケーション設定（データディレクトリなど）
│   ├── gui/                    # GUIコンポーネント
│   │   ├── __init__.py
│   │   ├── home_window.py     # ホーム画面（現在は未使用）
│   │   ├── conversation_window.py  # メイン画面（タブベースのUI）
│   │   ├── result_window.py   # 結果画面（開発中）
│   │   ├── history_window.py   # 履歴画面（開発中）
│   ├── services/              # サービス層
│   │   ├── __init__.py
│   │   ├── audio_service.py           # 音声録音・再生サービス
│   │   ├── api_check_service.py        # API接続状態チェックサービス
│   │   ├── openai_service.py          # OpenAI API連携（評価用）
│   │   ├── realtime_service.py        # OpenAI Realtime API連携
│   │   ├── evaluation_service.py      # 会話評価サービス
│   │   └── storage_service.py         # データ保存サービス
│   └── models/                # データモデル
│       ├── __init__.py
│       └── schemas.py         # データスキーマ定義
├── tests/                     # テストコード
├── pyproject.toml            # プロジェクト設定と依存関係
├── build_windows.spec        # PyInstaller設定ファイル
├── .cursorrules              # Cursorのプロジェクトルール
├── .cursor_memo/             # 開発メモ・ドキュメント（Cursorが作成するMarkdownファイルの保存場所）
│   ├── specifications.md     # プロジェクト仕様書
│   ├── TROUBLESHOOTING.md    # トラブルシューティングガイド
│   └── TEST_RESULTS.md      # テスト結果レポート
└── README.md                 # このファイル（プロジェクトルートに配置される唯一のMarkdownファイル）
```

**注意**: このプロジェクトでは、Cursorが自動的に作成するMarkdownファイル（レポート、メモ、ドキュメントなど）はすべて`.cursor_memo/`ディレクトリ以下に保存されます。プロジェクトのトップディレクトリには`README.md`のみを配置します。詳細は`.cursorrules`ファイルを参照してください。

## 実装状況

### 実装済み機能

- ✅ **メイン画面タブ**
  - API接続状態の確認
  - マイク・スピーカーのテスト
  - リアルタイム音声波形表示
  - テストデータの初期化

- ✅ **会話テストタブ**
  - OpenAI Realtime APIを使用したリアルタイム音声対話
  - ロールプレイシーンの選択
  - 会話履歴の記録と表示
  - 自動評価機能（文法・語彙・表現・流暢さ）
  - タイマー機能
  - 一時停止・中断機能
  - 評価データの自動保存

### 開発中機能

- 🚧 **リスニングテストタブ**: 音声を聞いて理解度を測定する機能
- 🚧 **結果画面**: 評価結果の詳細表示
- 🚧 **履歴画面**: 過去の評価履歴一覧と詳細表示

## 開発

### 依存関係の管理

このプロジェクトは`uv`を使用してパッケージを管理します。

```bash
# 依存関係のインストール
uv sync

# 開発依存関係を含めてインストール
uv sync --dev

# 新しいパッケージの追加
uv add <package-name>

# 開発用パッケージの追加
uv add --dev <package-name>
```

### コードスタイル

- Python 3.14の型ヒントを使用
- 関数とクラスにはdocstringを記述
- エラーハンドリングを適切に実装

### 主要な依存パッケージ

- **flet[all]**: GUIフレームワーク
- **openai**: OpenAI APIクライアント
- **sounddevice**: 音声入出力
- **numpy**: 数値計算
- **pydub**: 音声処理
- **pydantic**: データバリデーション
- **python-dotenv**: 環境変数管理

## ライセンス

このプロジェクトは開発中です。
