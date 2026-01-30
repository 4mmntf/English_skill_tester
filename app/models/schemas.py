"""
データモデル（スキーマ定義）
"""
from pydantic import BaseModel
from datetime import datetime


class EvaluationResult(BaseModel):
    """評価結果のデータモデル"""
    
    pronunciation_score: float | None = None  # 発音スコア
    accuracy_score: float | None = None  # 正確性スコア
    fluency_score: float | None = None  # 流暢さスコア
    completeness_score: float | None = None  # 完全性スコア
    overall_score: float | None = None  # 総合スコア
    feedback: str | None = None  # フィードバックテキスト
    timestamp: datetime | None = None  # 評価日時


class ConversationData(BaseModel):
    """会話データのデータモデル"""
    
    audio_data: bytes | None = None  # 音声データ（バイト列）
    text: str | None = None  # 会話テキスト
    reference_text: str | None = None  # 参照テキスト（発音評価用）

