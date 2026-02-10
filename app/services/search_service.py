"""
検索サービス
DuckDuckGo Searchを使用してWeb検索を行う機能を提供します。
"""

from typing import List, Dict, Any
import logging
from duckduckgo_search import DDGS


class SearchService:
    """DuckDuckGo Searchを使用するサービスクラス"""

    def __init__(self) -> None:
        """初期化処理"""
        pass

    def search(self, query: str, max_results: int = 3) -> str:
        """
        Web検索を実行し、結果をテキスト形式で返します。

        Args:
            query: 検索クエリ
            max_results: 最大検索結果数

        Returns:
            検索結果のサマリー（テキスト）
        """
        try:
            print(f"検索実行: {query}")
            results = []

            # DDGSコンテキストマネージャーを使用
            with DDGS() as ddgs:
                # テキスト検索を実行
                search_results = list(ddgs.text(query, max_results=max_results))

                for i, result in enumerate(search_results):
                    title = result.get("title", "No Title")
                    body = result.get("body", "No Description")
                    href = result.get("href", "")

                    results.append(
                        f"Result {i + 1}:\nTitle: {title}\nURL: {href}\nSummary: {body}\n"
                    )

            if not results:
                return "No search results found."

            return "\n".join(results)

        except Exception as e:
            error_msg = f"Search error: {str(e)}"
            print(error_msg)
            return error_msg
