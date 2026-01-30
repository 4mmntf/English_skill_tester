#!/bin/bash
# テスト実行スクリプト

set -e

echo "============================================================"
echo "テストスイートを実行します..."
echo "============================================================"

# 環境変数を設定（存在しない場合）
export OPENAI_API_KEY="${OPENAI_API_KEY:-dummy_key_for_testing}"
export OPENAI_API="${OPENAI_API:-dummy_key_for_testing}"

# 1. 基本的なインポートテスト
echo ""
echo "1. 基本的なインポートテスト"
echo "------------------------------------------------------------"
uv run python tests/test_imports.py || exit 1

# 2. 構文チェック
echo ""
echo "2. 構文チェック"
echo "------------------------------------------------------------"
uv run python -m py_compile app/main.py || exit 1
uv run python -m py_compile app/gui/conversation_window.py || exit 1
echo "✓ 構文チェック成功"

# 3. 基本的な機能テスト
echo ""
echo "3. 基本的な機能テスト"
echo "------------------------------------------------------------"
uv run python tests/test_conversation_window.py || exit 1

echo ""
echo "============================================================"
echo "すべてのテストが成功しました！"
echo "============================================================"

