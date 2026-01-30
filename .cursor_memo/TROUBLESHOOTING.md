# トラブルシューティング

## 依存関係のインストールエラー

### 問題

`uv sync`でエラーが発生する場合があります。

### 解決方法

```bash
# キャッシュをクリアして再インストール
uv cache clean
uv sync
```

## Fletの実行エラー

### 問題1: flet-desktopパッケージのインストールエラー

エラーメッセージ: `Unable to upgrade "flet-desktop" package`

### 解決方法

`flet[all]`をインストールする必要があります。`pyproject.toml`で`flet[all]`が指定されていることを確認してください：

```bash
# 依存関係を再インストール
uv sync
```

### 問題2: Fletアプリケーションが起動しない

### 解決方法

```bash
# Fletが正しくインストールされているか確認
uv run python -c "import flet; print('Flet imported successfully')"

# アプリケーションを実行
uv run python app/main.py
```

### 問題3: macOSでの実行時の注意

FletはmacOSで正常に動作しますが、初回実行時にセキュリティ警告が表示される場合があります。その場合は、システム環境設定で許可してください。

## その他の問題

### uvが見つからない

```bash
# macOS/Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# Windows
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

### 環境変数の設定

`.env`ファイルが正しく設定されているか確認してください：

```bash
# .envファイルの例
OPENAI_API_KEY=your_openai_api_key_here
AZURE_SPEECH_KEY=your_azure_speech_key_here
AZURE_SPEECH_REGION=your_azure_region_here
```
