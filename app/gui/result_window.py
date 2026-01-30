"""
結果画面のGUIコンポーネント
"""
import flet as ft


class ResultWindow:
    """結果画面のウィンドウクラス"""
    
    def __init__(self, page: ft.Page) -> None:
        """
        初期化処理
        
        Args:
            page: Fletのページオブジェクト
        """
        self.page = page

    def build(self) -> None:
        """ウィジェットの構築"""
        label = ft.Text(
            "結果画面",
            size=24,
            text_align=ft.TextAlign.CENTER
        )
        
        self.page.add(
            ft.Container(
                content=ft.Column(
                    [label],
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    alignment=ft.MainAxisAlignment.CENTER,
                ),
                expand=True,
            )
        )
