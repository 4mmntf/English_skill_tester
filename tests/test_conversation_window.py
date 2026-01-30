#!/usr/bin/env python3
"""
ConversationWindowの基本的な機能テスト
"""
import sys
import os
from pathlib import Path
from unittest.mock import Mock, MagicMock

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# 環境変数を設定（テスト用）
os.environ.setdefault("OPENAI_API_KEY", "dummy_key_for_testing")
os.environ.setdefault("OPENAI_API", "dummy_key_for_testing")

def test_conversation_window_initialization():
    """ConversationWindowの初期化テスト"""
    try:
        import flet as ft
        from app.gui.conversation_window import ConversationWindow
        
        # モックページを作成
        mock_page = Mock(spec=ft.Page)
        mock_page.window_width = 1920
        mock_page.window_height = 1080
        mock_page.window_min_width = 800
        mock_page.window_min_height = 600
        mock_page.window_full_screen = False
        mock_page.update = Mock()
        mock_page.overlay = []
        mock_page.add = Mock()
        
        # ConversationWindowを初期化
        window = ConversationWindow(mock_page)
        
        print("✓ ConversationWindowの初期化成功")
        
        # 基本的な属性が存在することを確認
        assert hasattr(window, 'test_items'), "test_items属性が存在しません"
        assert hasattr(window, 'storage_service'), "storage_service属性が存在しません"
        assert hasattr(window, 'audio_service'), "audio_service属性が存在しません"
        assert hasattr(window, 'api_check_service'), "api_check_service属性が存在しません"
        
        print("✓ 基本的な属性が存在することを確認")
        
        return True
    except Exception as e:
        print(f"✗ ConversationWindowの初期化失敗: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_conversation_window_build():
    """ConversationWindowのbuildメソッドテスト"""
    try:
        import flet as ft
        from app.gui.conversation_window import ConversationWindow
        
        # モックページを作成
        mock_page = Mock(spec=ft.Page)
        mock_page.window_width = 1920
        mock_page.window_height = 1080
        mock_page.window_min_width = 800
        mock_page.window_min_height = 600
        mock_page.window_full_screen = False
        mock_page.update = Mock()
        mock_page.overlay = []
        mock_page.add = Mock()
        
        window = ConversationWindow(mock_page)
        
        # buildメソッドを呼び出し（FletではbuildメソッドはNoneを返し、pageにコンテンツを追加する）
        try:
            window.build()
            # buildメソッドが正常に完了したことを確認（エラーが発生しなければ成功）
            assert mock_page.add.called, "buildメソッドがpage.add()を呼び出しませんでした"
            print("✓ ConversationWindowのbuildメソッド成功")
        except Exception as e:
            # buildメソッド内でエラーが発生した場合は失敗
            raise AssertionError(f"buildメソッドでエラーが発生しました: {e}")
        
        return True
    except Exception as e:
        print(f"✗ ConversationWindowのbuildメソッド失敗: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_storage_service():
    """StorageServiceの基本機能テスト"""
    try:
        from app.services.storage_service import LocalStorageService
        
        service = LocalStorageService()
        
        # データディレクトリが存在することを確認
        assert service.data_dir.exists() or service.data_dir.parent.exists(), "データディレクトリが存在しません"
        print("✓ LocalStorageServiceの初期化成功")
        
        return True
    except Exception as e:
        print(f"✗ LocalStorageServiceのテスト失敗: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_audio_service():
    """AudioServiceの基本機能テスト"""
    try:
        from app.services.audio_service import AudioService
        
        service = AudioService()
        
        # 基本的なメソッドが存在することを確認
        assert hasattr(service, 'start_mic_monitoring'), "start_mic_monitoringメソッドが存在しません"
        assert hasattr(service, 'stop_mic_monitoring'), "stop_mic_monitoringメソッドが存在しません"
        assert hasattr(service, 'record_audio'), "record_audioメソッドが存在しません"
        assert hasattr(service, 'play_audio'), "play_audioメソッドが存在しません"
        
        print("✓ AudioServiceの基本機能確認成功")
        
        return True
    except Exception as e:
        print(f"✗ AudioServiceのテスト失敗: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_api_check_service():
    """APICheckServiceの基本機能テスト"""
    try:
        from app.services.api_check_service import APICheckService
        
        service = APICheckService()
        
        # 基本的なメソッドが存在することを確認
        assert hasattr(service, 'check_all_apis'), "check_all_apisメソッドが存在しません"
        
        print("✓ APICheckServiceの基本機能確認成功")
        
        return True
    except Exception as e:
        print(f"✗ APICheckServiceのテスト失敗: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("ConversationWindowの機能テストを開始します...")
    print("=" * 60)
    
    results = []
    
    results.append(("StorageService", test_storage_service()))
    results.append(("AudioService", test_audio_service()))
    results.append(("APICheckService", test_api_check_service()))
    results.append(("ConversationWindow初期化", test_conversation_window_initialization()))
    results.append(("ConversationWindow build", test_conversation_window_build()))
    
    print("=" * 60)
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    print(f"テスト結果: {passed}/{total} 成功")
    
    if passed < total:
        print("\n失敗したテスト:")
        for name, result in results:
            if not result:
                print(f"  - {name}")
        sys.exit(1)
    else:
        print("すべてのテストが成功しました！")
        sys.exit(0)

