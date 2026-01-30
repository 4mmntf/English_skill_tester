"""
APICheckServiceのテスト
"""
import pytest
import os
from unittest.mock import patch, Mock
from app.services.api_check_service import APICheckService


class TestAPICheckService:
    """APICheckServiceのテストクラス"""
    
    @pytest.fixture
    def api_check_service(self):
        """APICheckServiceのインスタンスを作成"""
        return APICheckService()
    
    @patch.dict(os.environ, {}, clear=True)
    def test_check_openai_api_no_key(self, api_check_service):
        """APIキーが設定されていない場合のテスト"""
        result = api_check_service.check_openai_api()
        
        assert result["name"] == "OpenAI API"
        assert result["status"] == "不明"
        assert "APIキーが設定されていません" in result["message"]
    
    @patch.dict(os.environ, {"OPENAI_API_KEY": "test_key"})
    @patch('app.services.api_check_service.OpenAI')
    def test_check_openai_api_success(self, mock_openai, api_check_service):
        """OpenAI API接続成功のテスト"""
        mock_client = Mock()
        mock_client.models.list.return_value = []
        mock_openai.return_value = mock_client
        
        result = api_check_service.check_openai_api()
        
        assert result["name"] == "OpenAI API"
        assert result["status"] == "利用可能"
        assert "APIキーが有効です" in result["message"]
    
    @patch.dict(os.environ, {"OPENAI_API_KEY": "test_key"})
    @patch('app.services.api_check_service.OpenAI')
    def test_check_openai_api_error(self, mock_openai, api_check_service):
        """OpenAI API接続エラーのテスト"""
        mock_client = Mock()
        mock_client.models.list.side_effect = Exception("Connection error")
        mock_openai.return_value = mock_client
        
        result = api_check_service.check_openai_api()
        
        assert result["name"] == "OpenAI API"
        assert result["status"] == "エラー"
        assert "API接続エラー" in result["message"]
    
    @patch.dict(os.environ, {}, clear=True)
    def test_check_azure_speech_api_no_key(self, api_check_service):
        """Azure Speech APIキーが設定されていない場合のテスト"""
        result = api_check_service.check_azure_speech_api()
        
        assert result["name"] == "Azure Speech Service API"
        assert result["status"] == "不明"
        assert "APIキーまたはリージョンが設定されていません" in result["message"]
    
    @patch.dict(os.environ, {"AZURE_SPEECH_KEY": "test_key", "AZURE_SPEECH_REGION": "test_region"})
    @patch('app.services.api_check_service.speechsdk.SpeechConfig')
    def test_check_azure_speech_api_success(self, mock_speech_config, api_check_service):
        """Azure Speech API接続成功のテスト"""
        mock_speech_config.return_value = Mock()
        
        result = api_check_service.check_azure_speech_api()
        
        assert result["name"] == "Azure Speech Service API"
        assert result["status"] == "利用可能"
        assert "APIキーとリージョンが設定されています" in result["message"]
    
    @patch.dict(os.environ, {"AZURE_SPEECH_KEY": "test_key", "AZURE_SPEECH_REGION": "test_region"})
    @patch('app.services.api_check_service.speechsdk.SpeechConfig')
    def test_check_azure_speech_api_error(self, mock_speech_config, api_check_service):
        """Azure Speech API接続エラーのテスト"""
        mock_speech_config.side_effect = Exception("Connection error")
        
        result = api_check_service.check_azure_speech_api()
        
        assert result["name"] == "Azure Speech Service API"
        assert result["status"] == "エラー"
        assert "接続エラー" in result["message"]
    
    @patch.object(APICheckService, 'check_openai_api')
    @patch.object(APICheckService, 'check_azure_speech_api')
    def test_check_all_apis(self, mock_azure, mock_openai, api_check_service):
        """すべてのAPIチェックのテスト"""
        mock_openai.return_value = {"name": "OpenAI API", "status": "利用可能"}
        mock_azure.return_value = {"name": "Azure Speech API", "status": "利用可能"}
        
        results = api_check_service.check_all_apis()
        
        assert len(results) == 2
        assert mock_openai.called
        assert mock_azure.called

