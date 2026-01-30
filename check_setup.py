"""
セットアップ確認スクリプト
実行前に必要な依存関係がインストールされているか確認する
"""
import sys
from pathlib import Path

def check_imports() -> bool:
    """必要なモジュールのインポートを確認"""
    errors: list[str] = []
    
    # 標準ライブラリ
    try:
        import os
        import sys
        from pathlib import Path
        from typing import Dict, Any, List
        from datetime import datetime
        print("✓ 標準ライブラリ: OK")
    except ImportError as e:
        errors.append(f"標準ライブラリのインポートエラー: {e}")
        return False
    
    # 外部ライブラリ
    try:
        import customtkinter as ctk
        print("✓ customtkinter: OK")
    except ImportError:
        errors.append("customtkinter がインストールされていません。pip install customtkinter を実行してください。")
    
    try:
        from dotenv import load_dotenv
        print("✓ python-dotenv: OK")
    except ImportError:
        errors.append("python-dotenv がインストールされていません。pip install python-dotenv を実行してください。")
    
    try:
        from openai import OpenAI
        print("✓ openai: OK")
    except ImportError:
        errors.append("openai がインストールされていません。pip install openai を実行してください。")
    
    try:
        import azure.cognitiveservices.speech as speechsdk
        print("✓ azure-cognitiveservices-speech: OK")
    except ImportError:
        errors.append("azure-cognitiveservices-speech がインストールされていません。pip install azure-cognitiveservices-speech を実行してください。")
    
    try:
        from pydantic import BaseModel
        print("✓ pydantic: OK")
    except ImportError:
        errors.append("pydantic がインストールされていません。pip install pydantic を実行してください。")
    
    # アプリケーションモジュール
    try:
        sys.path.insert(0, str(Path(__file__).parent))
        from app.config import APP_DATA_DIR
        from app.models.schemas import EvaluationResult, ConversationData
        from app.services.storage_service import LocalStorageService
        from app.gui.home_window import HomeWindow
        print("✓ アプリケーションモジュール: OK")
    except ImportError as e:
        errors.append(f"アプリケーションモジュールのインポートエラー: {e}")
        return False
    
    if errors:
        print("\n❌ 以下の問題が見つかりました:")
        for error in errors:
            print(f"  - {error}")
        print("\n依存関係をインストールするには:")
        print("  uv sync")
        return False
    
    print("\n✓ 全ての依存関係が正しくインストールされています。")
    return True

def check_structure() -> bool:
    """プロジェクト構造を確認"""
    base_path = Path(__file__).parent
    required_files = [
        "app/main.py",
        "app/config.py",
        "app/models/schemas.py",
        "app/services/storage_service.py",
        "app/services/openai_service.py",
        "app/services/azure_service.py",
        "app/services/evaluation_service.py",
        "app/gui/home_window.py",
        "app/gui/conversation_window.py",
        "app/gui/result_window.py",
        "app/gui/history_window.py",
    ]
    
    missing_files: list[str] = []
    for file_path in required_files:
        if not (base_path / file_path).exists():
            missing_files.append(file_path)
    
    if missing_files:
        print("❌ 以下のファイルが見つかりません:")
        for file_path in missing_files:
            print(f"  - {file_path}")
        return False
    
    print("✓ プロジェクト構造: OK")
    return True

if __name__ == "__main__":
    print("=== セットアップ確認 ===\n")
    
    structure_ok = check_structure()
    print()
    imports_ok = check_imports()
    
    print("\n" + "=" * 40)
    if structure_ok and imports_ok:
        print("✓ セットアップは完了しています。")
        print("\n実行方法:")
        print("  uv run python app/main.py")
        print("  または")
        print("  python app/main.py")
        sys.exit(0)
    else:
        print("❌ セットアップに問題があります。")
        print("\n依存関係をインストールするには:")
        print("  uv sync")
        sys.exit(1)

