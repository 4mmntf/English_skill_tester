"""
評価サービス
複数の評価サービスを統合して総合的な評価を実行する
"""
from typing import Dict, Any
from datetime import datetime
from app.models.schemas import EvaluationResult
from app.services.openai_service import OpenAIService
from app.services.azure_service import AzurePronunciationService


class EvaluationService:
    """会話評価を統合的に実行するサービスクラス"""
    
    def __init__(self) -> None:
        """
        初期化処理
        OpenAIサービスとAzureサービスを初期化する
        Azure Speech APIの環境変数が設定されていない場合は、azure_serviceはNoneになる
        """
        self.openai_service: OpenAIService = OpenAIService()
        # Azure Speech APIの環境変数が設定されていない場合はNoneにする
        try:
            self.azure_service: AzurePronunciationService | None = AzurePronunciationService()
        except ValueError:
            # 環境変数が設定されていない場合はNoneを設定
            self.azure_service = None
            print("Azure Speech APIの環境変数が設定されていません。発音評価機能は使用できません。")

    async def evaluate_conversation(
        self,
        audio_data: bytes,
        conversation_text: str,
        reference_text: str | None = None
    ) -> EvaluationResult:
        """
        総合的な会話評価を実行
        
        Args:
            audio_data: 音声データ（バイト列）
            conversation_text: 会話テキスト
            reference_text: 参照テキスト（発音評価用、オプション）
        
        Returns:
            評価結果（EvaluationResultオブジェクト）
        """
        # Azure Pronunciation Assessmentで発音評価
        pronunciation_result: Dict[str, Any] | None = None
        if reference_text and self.azure_service:
            pronunciation_result = await self.azure_service.assess_pronunciation(
                audio_data, reference_text
            )
        
        # OpenAIで会話内容評価
        conversation_evaluation: Dict[str, Any] = await self.openai_service.evaluate_conversation(
            conversation_text
        )
        
        # 結果を統合
        overall_score: float | None = None
        pronunciation_score: float | None = None
        accuracy_score: float | None = None
        fluency_score: float | None = None
        completeness_score: float | None = None
        
        if pronunciation_result:
            pronunciation_score = pronunciation_result.get("pronunciation_score", 0)
            accuracy_score = pronunciation_result.get("accuracy_score", 0)
            fluency_score = pronunciation_result.get("fluency_score", 0)
            completeness_score = pronunciation_result.get("completeness_score", 0)
            
            # 総合スコアの計算（各スコアの平均）
            # Noneチェックを追加
            if pronunciation_score is not None and accuracy_score is not None and fluency_score is not None and completeness_score is not None:
                overall_score = (
                    pronunciation_score + accuracy_score + 
                    fluency_score + completeness_score
                ) / 4
        
        return EvaluationResult(
            pronunciation_score=pronunciation_score,
            accuracy_score=accuracy_score,
            fluency_score=fluency_score,
            completeness_score=completeness_score,
            overall_score=overall_score,
            feedback=conversation_evaluation.get("evaluation", ""),
            timestamp=datetime.now()
        )

