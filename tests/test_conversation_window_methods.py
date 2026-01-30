"""
ConversationWindowのメソッドテスト
"""
import pytest
import os
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime
import flet as ft
from app.gui.conversation_window import ConversationWindow


class TestConversationWindow:
    """ConversationWindowのテストクラス"""
    
    @pytest.fixture
    def mock_page(self):
        """モックページを作成"""
        page = Mock(spec=ft.Page)
        page.window_width = 1920
        page.window_height = 1080
        page.window_min_width = 800
        page.window_min_height = 600
        page.window_full_screen = False
        page.update = Mock()
        page.overlay = []
        page.add = Mock()
        return page
    
    @pytest.fixture
    def conversation_window(self, mock_page):
        """ConversationWindowのインスタンスを作成"""
        with patch.dict(os.environ, {"OPENAI_API_KEY": "dummy_key"}):
            window = ConversationWindow(mock_page)
            return window
    
    def test_format_conversation_history(self, conversation_window):
        """会話履歴のフォーマットテスト"""
        conversation_window.conversation_history = [
            {"role": "ai", "text": "Hello"},
            {"role": "student", "text": "Hi"},
            {"role": "ai", "text": "How are you?"},
        ]
        
        result = conversation_window._format_conversation_history()
        
        assert "AI「Hello」" in result
        assert "学生「Hi」" in result
        assert "AI「How are you?」" in result
    
    def test_format_conversation_history_empty(self, conversation_window):
        """空の会話履歴のフォーマットテスト"""
        conversation_window.conversation_history = []
        
        result = conversation_window._format_conversation_history()
        
        assert result == ""
    
    def test_disable_other_tabs(self, conversation_window):
        """他のタブを無効化するテスト"""
        conversation_window.tabs = Mock()
        conversation_window.tabs.unselected_label_color = ft.Colors.BLACK
        
        conversation_window._disable_other_tabs("conversation")
        
        assert conversation_window.tabs.unselected_label_color == ft.Colors.GREY_400
        assert conversation_window.page.update.called
    
    def test_enable_all_tabs(self, conversation_window):
        """すべてのタブを有効化するテスト"""
        conversation_window.tabs = Mock()
        conversation_window.tabs.unselected_label_color = ft.Colors.GREY_400
        
        conversation_window._enable_all_tabs()
        
        assert conversation_window.tabs.unselected_label_color == ft.Colors.BLACK
        assert conversation_window.page.update.called
    
    def test_on_tab_changed_main(self, conversation_window):
        """メイン画面タブへの変更テスト"""
        conversation_window.tabs = Mock()
        conversation_window.tabs.selected_index = 0
        conversation_window.test_items = [{"id": "main", "name": "メイン画面"}]
        conversation_window.test_running = False
        conversation_window._initialize_main_tab = Mock()
        
        event = Mock()
        conversation_window._on_tab_changed(event)
        
        assert conversation_window._initialize_main_tab.called
    
    def test_on_tab_changed_test_running(self, conversation_window):
        """テスト実行中のタブ変更テスト（変更を無効化）"""
        conversation_window.tabs = Mock()
        conversation_window.tabs.selected_index = 1
        conversation_window.test_running = True
        conversation_window.current_test_id = "conversation"
        conversation_window.test_items = [
            {"id": "main", "name": "メイン画面"},
            {"id": "conversation", "name": "会話テスト"},
        ]
        
        event = Mock()
        conversation_window._on_tab_changed(event)
        
        # テスト実行中はタブが変更されないことを確認
        assert conversation_window.tabs.selected_index == 1
    
    def test_on_reset_tests_clicked(self, conversation_window):
        """テストリセットのテスト"""
        conversation_window.storage_service.delete_test_progress = Mock()
        conversation_window.test_status_text = Mock()
        conversation_window.tab_timers = {
            "conversation": {"text": Mock(), "running": True}
        }
        conversation_window.overall_timer_text = Mock()
        conversation_window.tab_status_texts = {
            "conversation": Mock()
        }
        
        event = Mock()
        conversation_window._on_reset_tests_clicked(event)
        
        assert conversation_window.test_initialized is True
        assert conversation_window.storage_service.delete_test_progress.called
    
    def test_update_score_chart_empty(self, conversation_window):
        """空のスコアチャート更新テスト"""
        conversation_window.score_chart = Mock()
        conversation_window.score_chart.data_series = [Mock() for _ in range(5)]
        conversation_window.evaluation_scores_history = []
        
        conversation_window._update_score_chart()
        
        assert conversation_window.page.update.called
    
    def test_update_score_chart_with_data(self, conversation_window):
        """データがある場合のスコアチャート更新テスト"""
        conversation_window.score_chart = Mock()
        conversation_window.score_chart.data_series = [Mock() for _ in range(5)]
        conversation_window.evaluation_scores_history = [
            {"grammar": 85, "vocabulary": 80, "naturalness": 75, "fluency": 90, "overall": 82.5}
        ]
        
        conversation_window._update_score_chart()
        
        assert conversation_window.page.update.called
        assert conversation_window.score_chart.data_series[0].data_points is not None

