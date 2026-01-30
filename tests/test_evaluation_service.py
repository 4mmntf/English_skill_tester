"""
EvaluationServiceのテスト
"""
import pytest
from unittest.mock import patch, Mock, AsyncMock
from app.services.evaluation_service import EvaluationService
from app.models.schemas import EvaluationResult


class TestEvaluationService:
    """EvaluationServiceのテストクラス"""
    
    @pytest.fixture
    def evaluation_service(self):
        """EvaluationServiceのインスタンスを作成（Azureなし）"""
        with patch('app.services.evaluation_service.OpenAIService'):
            with patch('app.services.evaluation_service.AzurePronunciationService', side_effect=ValueError("No env vars")):
                service = EvaluationService()
                yield service
    
    @pytest.fixture
    def evaluation_service_with_azure(self):
        """EvaluationServiceのインスタンスを作成（Azureあり）"""
        with patch('app.services.evaluation_service.OpenAIService'):
            with patch('app.services.evaluation_service.AzurePronunciationService') as mock_azure:
                mock_azure.return_value = Mock()
                service = EvaluationService()
                service.azure_service = mock_azure.return_value
                yield service
    
    @pytest.mark.asyncio
    async def test_evaluate_conversation_without_azure(self, evaluation_service):
        """Azureなしで会話評価を実行"""
        # OpenAIサービスのモック
        mock_openai_result = {
            "evaluation": "Good conversation",
            "is_valid": True,
            "grammar_score": 85,
            "vocabulary_score": 80,
            "naturalness_score": 75,
            "fluency_score": 90,
            "overall_score": 82.5,
        }
        evaluation_service.openai_service.evaluate_conversation = AsyncMock(return_value=mock_openai_result)
        
        result = await evaluation_service.evaluate_conversation(
            audio_data=b"dummy_audio",
            conversation_text="AI「Hello」\n学生「Hi」"
        )
        
        assert isinstance(result, EvaluationResult)
        assert result.feedback == "Good conversation"
        assert result.pronunciation_score is None
        assert result.accuracy_score is None
        assert result.fluency_score is None
        assert result.completeness_score is None
        assert result.overall_score is None
    
    @pytest.mark.asyncio
    async def test_evaluate_conversation_with_azure(self, evaluation_service_with_azure):
        """Azureありで会話評価を実行"""
        # OpenAIサービスのモック
        mock_openai_result = {
            "evaluation": "Good conversation",
            "is_valid": True,
            "grammar_score": 85,
            "vocabulary_score": 80,
            "naturalness_score": 75,
            "fluency_score": 90,
            "overall_score": 82.5,
        }
        evaluation_service_with_azure.openai_service.evaluate_conversation = AsyncMock(return_value=mock_openai_result)
        
        # Azureサービスのモック
        mock_azure_result = {
            "pronunciation_score": 88,
            "accuracy_score": 85,
            "fluency_score": 90,
            "completeness_score": 87,
        }
        evaluation_service_with_azure.azure_service.assess_pronunciation = AsyncMock(return_value=mock_azure_result)
        
        result = await evaluation_service_with_azure.evaluate_conversation(
            audio_data=b"dummy_audio",
            conversation_text="AI「Hello」\n学生「Hi」",
            reference_text="Hello"
        )
        
        assert isinstance(result, EvaluationResult)
        assert result.pronunciation_score == 88
        assert result.accuracy_score == 85
        assert result.fluency_score == 90
        assert result.completeness_score == 87
        assert result.overall_score is not None
        assert result.feedback == "Good conversation"
    
    @pytest.mark.asyncio
    async def test_evaluate_conversation_azure_none_values(self, evaluation_service_with_azure):
        """Azure結果にNone値が含まれる場合のテスト"""
        # OpenAIサービスのモック
        mock_openai_result = {
            "evaluation": "Good conversation",
            "is_valid": True,
            "grammar_score": 85,
            "vocabulary_score": 80,
            "naturalness_score": 75,
            "fluency_score": 90,
            "overall_score": 82.5,
        }
        evaluation_service_with_azure.openai_service.evaluate_conversation = AsyncMock(return_value=mock_openai_result)
        
        # Azureサービスのモック（None値を含む）
        mock_azure_result = {
            "pronunciation_score": None,
            "accuracy_score": 85,
            "fluency_score": None,
            "completeness_score": 87,
        }
        evaluation_service_with_azure.azure_service.assess_pronunciation = AsyncMock(return_value=mock_azure_result)
        
        result = await evaluation_service_with_azure.evaluate_conversation(
            audio_data=b"dummy_audio",
            conversation_text="AI「Hello」\n学生「Hi」",
            reference_text="Hello"
        )
        
        assert isinstance(result, EvaluationResult)
        assert result.pronunciation_score is None
        assert result.overall_score is None  # None値があるため計算されない

