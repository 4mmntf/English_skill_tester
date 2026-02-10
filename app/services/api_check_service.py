"""
API接続チェックサービス
各種LLM APIの接続状態をチェックする
"""

import os
from typing import Dict, List
from openai import OpenAI


class APICheckService:
    """API接続状態をチェックするサービスクラス"""

    def __init__(self) -> None:
        """初期化処理"""
        pass

    def check_openai_api(self) -> Dict[str, str]:
        """
        OpenAI APIの接続状態をチェック

        Returns:
            API名と状態を含む辞書
        """
        # OPENAI_API_KEYまたはOPENAI_APIのどちらかをサポート
        api_key: str | None = os.getenv("OPENAI_API_KEY") or os.getenv("OPENAI_API")

        if not api_key:
            return {
                "name": "OpenAI API",
                "status": "不明",
                "message": "APIキーが設定されていません",
            }

        try:
            client = OpenAI(api_key=api_key)
            # 簡単なリクエストで接続確認（models.list()を呼び出して確認）
            try:
                models = client.models.list()
                return {
                    "name": "OpenAI API",
                    "status": "利用可能",
                    "message": "APIキーが有効です",
                }
            except Exception as e:
                return {
                    "name": "OpenAI API",
                    "status": "エラー",
                    "message": f"API接続エラー: {str(e)}",
                }
        except Exception as e:
            return {
                "name": "OpenAI API",
                "status": "エラー",
                "message": f"初期化エラー: {str(e)}",
            }

    def check_openrouter_api(self) -> Dict[str, str]:
        """
        OpenRouter APIの接続状態をチェック

        Returns:
            API名と状態を含む辞書
        """
        api_key: str | None = os.getenv("OPENROUTER_API_KEY")

        if not api_key:
            return {
                "name": "OpenRouter API",
                "status": "不明",
                "message": "APIキーが設定されていません",
            }

        try:
            # OpenRouterはOpenAI互換APIとして利用可能
            # base_urlを指定して接続確認
            client = OpenAI(api_key=api_key, base_url="https://openrouter.ai/api/v1")
            # 簡単なリクエストで接続確認
            try:
                models = client.models.list()
                return {
                    "name": "OpenRouter API",
                    "status": "利用可能",
                    "message": "APIキーが有効です",
                }
            except Exception as e:
                return {
                    "name": "OpenRouter API",
                    "status": "エラー",
                    "message": f"API接続エラー: {str(e)}",
                }
        except Exception as e:
            return {
                "name": "OpenRouter API",
                "status": "エラー",
                "message": f"初期化エラー: {str(e)}",
            }

    def check_all_apis(self) -> List[Dict[str, str]]:
        """
        全てのAPIの接続状態をチェック

        Returns:
            API状態のリスト
        """
        results: List[Dict[str, str]] = []

        # OpenAI APIのチェック
        results.append(self.check_openai_api())

        # OpenRouter APIのチェック
        results.append(self.check_openrouter_api())

        return results
