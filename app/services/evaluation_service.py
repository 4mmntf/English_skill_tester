"""
評価サービス
複数の評価サービスを統合して総合的な評価を実行する
"""

from typing import Dict, Any
from datetime import datetime
import os
from app.models.schemas import EvaluationResult
from app.services.openai_service import OpenAIService


class EvaluationService:
    """会話評価を統合的に実行するサービスクラス"""

    def __init__(self) -> None:
        """
        初期化処理
        OpenAIサービスを初期化する
        OpenRouter APIの環境変数が設定されていない場合は警告を表示する
        """
        self.openai_service: OpenAIService = OpenAIService()

        # OpenRouter APIのチェック
        if not os.getenv("OPENROUTER_API_KEY"):
            print(
                "OpenRouter APIの環境変数が設定されていません。リスニングテストはスキップされます。"
            )

    async def evaluate_conversation(
        self,
        audio_data: bytes,
        conversation_text: str,
        reference_text: str | None = None,
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
        # OpenAIで会話内容評価
        conversation_evaluation: Dict[
            str, Any
        ] = await self.openai_service.evaluate_conversation(conversation_text)

        # 結果を統合
        overall_score: float | None = None
        pronunciation_score: float | None = None
        accuracy_score: float | None = None
        fluency_score: float | None = None
        completeness_score: float | None = None

        # 将来的に他のスコア計算ロジックを追加可能

        return EvaluationResult(
            pronunciation_score=pronunciation_score,
            accuracy_score=accuracy_score,
            fluency_score=fluency_score,
            completeness_score=completeness_score,
            overall_score=overall_score,
            feedback=conversation_evaluation.get("evaluation", ""),
            vocabulary_info=conversation_evaluation.get("vocabulary_info", []),
            timestamp=datetime.now(),
        )

    async def predict_total_score(
        self,
        conversation_text: str,
        listening_results: list[Dict[str, Any]],
        grammar_results: list[Dict[str, Any]] | None = None,
    ) -> Dict[str, Any]:
        """
        総合スコア予測を実行

        Args:
            conversation_text: 会話テキスト
            listening_results: リスニングテスト結果
            grammar_results: 文法テスト結果（オプション）

        Returns:
            予測スコア情報
        """
        return await self.openai_service.predict_total_score(
            conversation_text, listening_results, grammar_results
        )
