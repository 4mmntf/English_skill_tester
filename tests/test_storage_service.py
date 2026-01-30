"""
LocalStorageServiceのテスト
"""
import pytest
import json
import tempfile
import shutil
from pathlib import Path
from unittest.mock import patch, mock_open
from app.services.storage_service import LocalStorageService
from app.config import APP_DATA_DIR


class TestLocalStorageService:
    """LocalStorageServiceのテストクラス"""
    
    @pytest.fixture
    def temp_data_dir(self):
        """一時的なデータディレクトリを作成"""
        temp_dir = Path(tempfile.mkdtemp())
        yield temp_dir
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def storage_service(self, temp_data_dir):
        """LocalStorageServiceのインスタンスを作成"""
        with patch('app.services.storage_service.APP_DATA_DIR', temp_data_dir):
            with patch('app.config.APP_DATA_DIR', temp_data_dir):
                service = LocalStorageService()
                yield service
    
    def test_init(self, storage_service):
        """初期化テスト"""
        assert storage_service.data_dir.exists()
        assert storage_service.data_dir.is_dir()
    
    def test_save_evaluation_data_with_filename(self, storage_service):
        """ファイル名を指定して評価データを保存"""
        data = {"test": "data", "score": 85}
        filename = "test_evaluation.json"
        
        result = storage_service.save_evaluation_data(data, filename)
        
        assert result is True
        file_path = storage_service.data_dir / filename
        assert file_path.exists()
        
        with open(file_path, 'r', encoding='utf-8') as f:
            loaded_data = json.load(f)
        assert loaded_data == data
    
    def test_save_evaluation_data_without_filename(self, storage_service):
        """ファイル名を指定せずに評価データを保存（タイムスタンプから自動生成）"""
        data = {"test": "data", "score": 85}
        
        result = storage_service.save_evaluation_data(data)
        
        assert result is True
        # タイムスタンプから生成されたファイルが存在することを確認
        json_files = list(storage_service.data_dir.glob("evaluation_*.json"))
        assert len(json_files) == 1
    
    def test_save_evaluation_data_failure(self, storage_service):
        """保存失敗時のテスト"""
        # 読み取り専用ディレクトリで保存を試みる（権限エラーをシミュレート）
        with patch('builtins.open', side_effect=PermissionError("Permission denied")):
            data = {"test": "data"}
            result = storage_service.save_evaluation_data(data, "test.json")
            assert result is False
    
    def test_list_evaluation_history(self, storage_service):
        """評価履歴のリスト取得テスト"""
        # テストデータを保存
        data1 = {"test": "data1", "score": 80}
        data2 = {"test": "data2", "score": 90}
        storage_service.save_evaluation_data(data1, "test1.json")
        storage_service.save_evaluation_data(data2, "test2.json")
        
        history = storage_service.list_evaluation_history()
        
        assert len(history) == 2
        assert all("filename" in item for item in history)
        assert all("path" in item for item in history)
        assert all("modified" in item for item in history)
        assert all("size" in item for item in history)
    
    def test_list_evaluation_history_empty(self, storage_service):
        """評価履歴が空の場合のテスト"""
        history = storage_service.list_evaluation_history()
        assert history == []
    
    def test_load_evaluation_data(self, storage_service):
        """評価データの読み込みテスト"""
        data = {"test": "data", "score": 85}
        filename = "test_evaluation.json"
        storage_service.save_evaluation_data(data, filename)
        
        loaded_data = storage_service.load_evaluation_data(filename)
        
        assert loaded_data == data
    
    def test_load_evaluation_data_not_found(self, storage_service):
        """存在しないファイルの読み込みテスト"""
        loaded_data = storage_service.load_evaluation_data("nonexistent.json")
        assert loaded_data is None
    
    def test_save_test_progress(self, storage_service, temp_data_dir):
        """テスト進捗の保存テスト"""
        test_id = "conversation"
        progress_data = {"test_id": test_id, "final_time": "00:05:30"}
        
        result = storage_service.save_test_progress(test_id, progress_data)
        
        assert result is True
        progress_dir = temp_data_dir / "test_progress"
        file_path = progress_dir / f"{test_id}_progress.json"
        assert file_path.exists()
    
    def test_load_test_progress(self, storage_service, temp_data_dir):
        """テスト進捗の読み込みテスト"""
        test_id = "conversation"
        progress_data = {"test_id": test_id, "final_time": "00:05:30"}
        storage_service.save_test_progress(test_id, progress_data)
        
        loaded_progress = storage_service.load_test_progress(test_id)
        
        assert loaded_progress == progress_data
    
    def test_load_test_progress_not_found(self, storage_service):
        """存在しないテスト進捗の読み込みテスト"""
        loaded_progress = storage_service.load_test_progress("nonexistent")
        assert loaded_progress is None
    
    def test_delete_test_progress_specific(self, storage_service, temp_data_dir):
        """特定のテスト進捗の削除テスト"""
        test_id = "conversation"
        progress_data = {"test_id": test_id, "final_time": "00:05:30"}
        storage_service.save_test_progress(test_id, progress_data)
        
        result = storage_service.delete_test_progress(test_id)
        
        assert result is True
        loaded_progress = storage_service.load_test_progress(test_id)
        assert loaded_progress is None
    
    def test_delete_test_progress_all(self, storage_service, temp_data_dir):
        """すべてのテスト進捗の削除テスト"""
        # 複数のテスト進捗を保存
        storage_service.save_test_progress("conversation", {"test": "data1"})
        storage_service.save_test_progress("pronunciation", {"test": "data2"})
        
        result = storage_service.delete_test_progress()
        
        assert result is True
        assert storage_service.load_test_progress("conversation") is None
        assert storage_service.load_test_progress("pronunciation") is None
    
    def test_has_test_progress_true(self, storage_service, temp_data_dir):
        """テスト進捗が存在する場合のテスト"""
        storage_service.save_test_progress("conversation", {"test": "data"})
        
        result = storage_service.has_test_progress()
        
        assert result is True
    
    def test_has_test_progress_false(self, storage_service):
        """テスト進捗が存在しない場合のテスト"""
        result = storage_service.has_test_progress()
        assert result is False

