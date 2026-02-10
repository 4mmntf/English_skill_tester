"""
OpenAIServiceのテスト
"""

import pytest
import os
import json
from unittest.mock import patch, Mock, AsyncMock
from app.services.openai_service import OpenAIService


class TestOpenAIService:
    """OpenAIServiceのテストクラス"""

    @pytest.fixture
    def mock_openai_client(self):
        """モックOpenAIクライアント"""
        return Mock()

    @patch.dict(os.environ, {"OPENAI_API_KEY": "test_key"})
    @patch("app.services.openai_service.OpenAI")
    def test_init_success(self, mock_openai):
        """初期化成功のテスト"""
        mock_openai.return_value = Mock()

        service = OpenAIService()

        assert service.client is not None
        assert service.model == os.getenv("OPENAI_MODEL", "gpt-4o-mini")

    @patch.dict(os.environ, {}, clear=True)
    def test_init_failure_no_key(self):
        """APIキーが設定されていない場合の初期化失敗テスト"""
        with pytest.raises(
            ValueError,
            match="OPENAI_API_KEYまたはOPENAI_API環境変数が設定されていません",
        ):
            OpenAIService()

    @pytest.mark.asyncio
    @patch.dict(os.environ, {"OPENAI_API_KEY": "test_key"})
    @patch("app.services.openai_service.OpenAI")
    async def test_evaluate_conversation_success(self, mock_openai):
        """会話評価成功のテスト"""
        # モックレスポンスを設定
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = json.dumps(
            {
                "is_valid": True,
                "grammar_score": 85,
                "vocabulary_score": 80,
                "naturalness_score": 75,
                "fluency_score": 90,
                "overall_score": 82.5,
                "feedback": "Good conversation",
            }
        )

        mock_client = Mock()
        mock_client.chat.completions.create = Mock(return_value=mock_response)
        mock_openai.return_value = mock_client

        service = OpenAIService()
        result = await service.evaluate_conversation("AI「Hello」\n学生「Hi」")

        assert "error" not in result
        assert result["is_valid"] is True
        assert result["grammar_score"] == 85
        assert result["vocabulary_score"] == 80
        assert result["naturalness_score"] == 75
        assert result["fluency_score"] == 90
        assert result["overall_score"] == 82.5
        assert result["evaluation"] == "Good conversation"

    @pytest.mark.asyncio
    @patch.dict(os.environ, {"OPENAI_API_KEY": "test_key"})
    @patch("app.services.openai_service.OpenAI")
    async def test_evaluate_conversation_json_error(self, mock_openai):
        """JSON解析エラーのテスト"""
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = "Invalid JSON"

        mock_client = Mock()
        mock_client.chat.completions.create = Mock(return_value=mock_response)
        mock_openai.return_value = mock_client

        service = OpenAIService()
        result = await service.evaluate_conversation("AI「Hello」\n学生「Hi」")

        assert "error" in result
        assert result["is_valid"] is False

    @pytest.mark.asyncio
    @patch.dict(os.environ, {"OPENAI_API_KEY": "test_key"})
    @patch("app.services.openai_service.OpenAI")
    async def test_evaluate_conversation_api_error(self, mock_openai):
        """APIエラーのテスト"""
        mock_client = Mock()
        mock_client.chat.completions.create = Mock(side_effect=Exception("API Error"))
        mock_openai.return_value = mock_client

        service = OpenAIService()
        result = await service.evaluate_conversation("AI「Hello」\n学生「Hi」")

        assert "error" in result
        assert result["is_valid"] is False
        assert "API Error" in result["error"]

    @pytest.mark.asyncio
    @patch.dict(os.environ, {"OPENAI_API_KEY": "test_key"})
    @patch("app.services.openai_service.OpenAI")
    async def test_evaluate_conversation_with_vocabulary(self, mock_openai):
        """単語情報を含む会話評価成功のテスト"""
        # モックレスポンスを設定
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = json.dumps(
            {
                "is_valid": True,
                "grammar_score": 85,
                "vocabulary_score": 80,
                "naturalness_score": 75,
                "fluency_score": 90,
                "overall_score": 82.5,
                "feedback": "Good conversation",
                "vocabulary_info": [
                    {
                        "word": "ubiquitous",
                        "definition": "至る所にある",
                        "example": "Smartphones are ubiquitous these days.",
                    }
                ],
            }
        )

        mock_client = Mock()
        mock_client.chat.completions.create = Mock(return_value=mock_response)
        mock_openai.return_value = mock_client

        service = OpenAIService()
        result = await service.evaluate_conversation("AI「Hello」\n学生「Hi」")

        assert "error" not in result
        assert result["is_valid"] is True
        assert len(result["vocabulary_info"]) == 1
        assert result["vocabulary_info"][0]["word"] == "ubiquitous"
        assert result["vocabulary_info"][0]["definition"] == "至る所にある"

    @pytest.mark.asyncio
    @patch.dict(os.environ, {"OPENAI_API_KEY": "test_key"})
    @patch("app.services.openai_service.OpenAI")
    async def test_evaluate_conversation_empty_response(self, mock_openai):
        """空のレスポンスのテスト"""
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = None

        mock_client = Mock()
        mock_client.chat.completions.create = Mock(return_value=mock_response)
        mock_openai.return_value = mock_client

        service = OpenAIService()
        result = await service.evaluate_conversation("AI「Hello」\n学生「Hi」")

        assert "error" in result
        assert result["is_valid"] is False
        assert "レスポンスが空" in result["error"]
