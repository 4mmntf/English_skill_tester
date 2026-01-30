"""
OpenAI APIサービス
"""
import os
from openai import OpenAI
from typing import Dict, Any


class OpenAIService:
    """OpenAI APIを使用するサービスクラス"""
    
    def __init__(self) -> None:
        """
        初期化処理
        環境変数からAPIキーを取得し、OpenAIクライアントを初期化する
        """
        # OPENAI_API_KEYまたはOPENAI_APIのどちらかをサポート
        api_key: str | None = os.getenv("OPENAI_API_KEY") or os.getenv("OPENAI_API")
        if not api_key:
            raise ValueError("OPENAI_API_KEYまたはOPENAI_API環境変数が設定されていません")
        self.client: OpenAI = OpenAI(api_key=api_key)
        # 開発中はGPT-5 nano/miniを使用
        self.model: str = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

    async def get_realtime_response(self, audio_data: bytes) -> str | None:
        """
        Realtime APIを使用して音声データから応答を取得
        
        Args:
            audio_data: 音声データ（バイト列）
        
        Returns:
            AIからの応答テキスト、失敗時はNone
        """
        # TODO: Realtime APIの実装
        pass

    async def evaluate_conversation(self, conversation_text: str) -> Dict[str, Any]:
        """
        GPT-5を使用して会話内容を評価
        
        Args:
            conversation_text: 評価する会話テキスト（AIと学生の会話を交互に記録した形式）
        
        Returns:
            評価結果を含む辞書（"evaluation"キーに評価内容、"is_valid"キーに会話が成立しているかの判定、エラー時は"error"キーにエラーメッセージ）
        """
        prompt: str = f"""
        以下の英会話を評価してください。以下の観点で評価をお願いします：
        1. 会話として成立しているか（お互いの意図が伝わっているか、適切な応答ができているか）
        2. 文法の正確性
        3. 語彙の適切性
        4. 会話の自然さ
        5. 会話の流暢さ
        
        会話内容：
        {conversation_text}
        
        評価結果を以下のJSON形式で返してください：
        {{
            "is_valid": true/false,  // 会話として成立しているか
            "grammar_score": 0-100,  // 文法の正確性スコア
            "vocabulary_score": 0-100,  // 語彙の適切性スコア
            "naturalness_score": 0-100,  // 会話の自然さスコア
            "fluency_score": 0-100,  // 会話の流暢さスコア
            "overall_score": 0-100,  // 総合スコア
            "feedback": "評価コメント"
        }}
        """
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are an English conversation evaluation expert. Always respond in valid JSON format."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                response_format={"type": "json_object"},  # JSON形式で返すことを強制
            )
            content: str | None = response.choices[0].message.content
            if content:
                import json
                try:
                    evaluation_data = json.loads(content)
                    return {
                        "evaluation": evaluation_data.get("feedback", ""),
                        "is_valid": evaluation_data.get("is_valid", False),
                        "grammar_score": evaluation_data.get("grammar_score", 0),
                        "vocabulary_score": evaluation_data.get("vocabulary_score", 0),
                        "naturalness_score": evaluation_data.get("naturalness_score", 0),
                        "fluency_score": evaluation_data.get("fluency_score", 0),
                        "overall_score": evaluation_data.get("overall_score", 0),
                    }
                except json.JSONDecodeError:
                    return {"evaluation": content, "is_valid": False, "error": "JSON解析エラー"}
            return {"evaluation": "", "is_valid": False, "error": "レスポンスが空"}
        except Exception as e:
            return {"error": str(e), "is_valid": False}

