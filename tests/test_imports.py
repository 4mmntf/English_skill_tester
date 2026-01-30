#!/usr/bin/env python3
"""
基本的なインポートテスト
すべての主要モジュールが正しくインポートできることを確認する
"""
import sys
from pathlib import Path

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def test_imports():
    """すべての主要モジュールのインポートをテスト"""
    errors = []
    
    # 基本モジュール
    try:
        import app.config
        print("✓ app.config インポート成功")
    except Exception as e:
        errors.append(f"app.config: {e}")
        print(f"✗ app.config インポート失敗: {e}")
    
    # サービスモジュール
    services = [
        "app.services.storage_service",
        "app.services.audio_service",
        "app.services.api_check_service",
        "app.services.openai_service",
        "app.services.evaluation_service",
        "app.services.realtime_service",
        "app.services.azure_service",
    ]
    
    for service in services:
        try:
            __import__(service)
            print(f"✓ {service} インポート成功")
        except Exception as e:
            errors.append(f"{service}: {e}")
            print(f"✗ {service} インポート失敗: {e}")
    
    # モデルモジュール
    try:
        import app.models.schemas
        print("✓ app.models.schemas インポート成功")
    except Exception as e:
        errors.append(f"app.models.schemas: {e}")
        print(f"✗ app.models.schemas インポート失敗: {e}")
    
    # GUIモジュール（Fletが必要）
    gui_modules = [
        "app.gui.conversation_window",
        "app.gui.home_window",
    ]
    
    for gui_module in gui_modules:
        try:
            __import__(gui_module)
            print(f"✓ {gui_module} インポート成功")
        except Exception as e:
            errors.append(f"{gui_module}: {e}")
            print(f"✗ {gui_module} インポート失敗: {e}")
    
    # メインモジュール
    try:
        import app.main
        print("✓ app.main インポート成功")
    except Exception as e:
        errors.append(f"app.main: {e}")
        print(f"✗ app.main インポート失敗: {e}")
    
    return errors

if __name__ == "__main__":
    print("=" * 60)
    print("基本的なインポートテストを開始します...")
    print("=" * 60)
    
    errors = test_imports()
    
    print("=" * 60)
    if errors:
        print(f"エラーが {len(errors)} 件見つかりました:")
        for error in errors:
            print(f"  - {error}")
        sys.exit(1)
    else:
        print("すべてのインポートテストが成功しました！")
        sys.exit(0)

