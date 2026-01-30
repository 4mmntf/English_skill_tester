"""
Azure Pronunciation Assessmentサービス
"""
import os
import azure.cognitiveservices.speech as speechsdk
from typing import Dict, Any


class AzurePronunciationService:
    """Azure Pronunciation Assessmentを使用するサービスクラス"""
    
    def __init__(self) -> None:
        """
        初期化処理
        環境変数からAzure Speech Serviceのキーとリージョンを取得し、設定する
        """
        self.speech_key: str | None = os.getenv("AZURE_SPEECH_KEY")
        self.speech_region: str | None = os.getenv("AZURE_SPEECH_REGION")
        
        if not self.speech_key or not self.speech_region:
            raise ValueError("AZURE_SPEECH_KEYとAZURE_SPEECH_REGION環境変数が設定されていません")
        
        self.speech_config: speechsdk.SpeechConfig = speechsdk.SpeechConfig(
            subscription=self.speech_key,
            region=self.speech_region
        )

    async def assess_pronunciation(
        self, 
        audio_data: bytes, 
        reference_text: str
    ) -> Dict[str, Any] | None:
        """
        Azure Pronunciation Assessmentを使用して発音を評価
        
        Args:
            audio_data: 評価する音声データ（バイト列）
            reference_text: 参照テキスト（正しい発音のテキスト）
        
        Returns:
            評価結果を含む辞書（発音スコア、正確性スコア、流暢さスコア、完全性スコアを含む）、
            認識失敗時はNone
        """
        # Pronunciation assessmentの設定
        pronunciation_config: speechsdk.PronunciationAssessmentConfig = speechsdk.PronunciationAssessmentConfig(
            reference_text=reference_text,
            grading_system=speechsdk.PronunciationAssessmentGradingSystem.HundredMark,
            granularity=speechsdk.PronunciationAssessmentGranularity.Phoneme,
            enable_miscue=True
        )
        
        pronunciation_config.apply_to(self.speech_config)
        
        # 音声認識の実行
        audio_stream: speechsdk.audio.PushAudioInputStream = speechsdk.audio.PushAudioInputStream()
        audio_stream.write(audio_data)
        audio_stream.close()
        
        audio_config: speechsdk.audio.AudioConfig = speechsdk.audio.AudioConfig(stream=audio_stream)
        speech_recognizer: speechsdk.SpeechRecognizer = speechsdk.SpeechRecognizer(
            speech_config=self.speech_config,
            audio_config=audio_config
        )
        
        result: speechsdk.SpeechRecognitionResult = speech_recognizer.recognize_once()
        
        if result.reason == speechsdk.ResultReason.RecognizedSpeech:
            pronunciation_result: speechsdk.PronunciationAssessmentResult = speechsdk.PronunciationAssessmentResult(result)
            return {
                "pronunciation_score": pronunciation_result.pronunciation_score,
                "accuracy_score": pronunciation_result.accuracy_score,
                "fluency_score": pronunciation_result.fluency_score,
                "completeness_score": pronunciation_result.completeness_score,
                "pronunciation_assessment": {
                    "accuracy_score": pronunciation_result.accuracy_score,
                    "pronunciation_score": pronunciation_result.pronunciation_score,
                    "completeness_score": pronunciation_result.completeness_score,
                    "fluency_score": pronunciation_result.fluency_score
                }
            }
        else:
            return None

