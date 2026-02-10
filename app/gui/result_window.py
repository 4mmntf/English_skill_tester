"""
結果画面のGUIコンポーネント
"""

import flet as ft
from typing import Callable, Any


class ResultWindow:
    """結果画面のウィンドウクラス"""

    def __init__(
        self,
        page: ft.Page,
        result_data: dict[str, Any],
        on_back_callback: Callable[[], None] | None = None,
    ) -> None:
        """
        初期化処理

        Args:
            page: Fletのページオブジェクト
            result_data: 評価結果データ
                {
                    "grammar_score": int,
                    "vocabulary_score": int,
                    "naturalness_score": int,
                    "fluency_score": int,
                    "overall_score": int,
                    "feedback": str
                }
            on_back_callback: 戻るボタンが押されたときのコールバック
        """
        self.page = page
        self.result_data = result_data
        self.on_back_callback = on_back_callback

    def build(self) -> None:
        """ウィジェットの構築"""
        self.page.clean()

        # タイトル
        title = ft.Text(
            "会話テスト結果",
            size=32,
            weight=ft.FontWeight.BOLD,
            text_align=ft.TextAlign.CENTER,
            color=ft.colors.BLACK,
        )

        # スコア表示コンポーネント作成
        score_chart = self._create_score_chart()

        # 詳細スコアカード作成
        score_details = self._create_score_details()

        # フィードバック表示
        feedback_section = self._create_feedback_section()

        # 戻るボタン
        back_button = ft.ElevatedButton(
            "会話画面に戻る",
            on_click=self._on_back_clicked,
            width=200,
            height=50,
            bgcolor=ft.colors.BLUE_400,
            color=ft.colors.WHITE,
        )

        content = ft.Container(
            content=ft.Column(
                [
                    ft.Container(height=20),
                    title,
                    ft.Container(height=30),
                    ft.Row(
                        [
                            score_chart,
                            ft.Container(width=40),
                            score_details,
                        ],
                        alignment=ft.MainAxisAlignment.CENTER,
                        vertical_alignment=ft.CrossAxisAlignment.START,
                    ),
                    ft.Container(height=30),
                    feedback_section,
                    ft.Container(height=30),
                    back_button,
                    ft.Container(height=20),
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                scroll=ft.ScrollMode.AUTO,
            ),
            padding=40,
            expand=True,
            bgcolor=ft.colors.WHITE,
        )

        self.page.add(content)
        self.page.update()

    def _create_score_chart(self) -> ft.Container:
        """レーダーチャート風の表示（FletにRadarChartがないので棒グラフで代用）を作成"""
        scores = [
            ("文法", self.result_data.get("grammar_score", 0), ft.colors.BLUE),
            ("語彙", self.result_data.get("vocabulary_score", 0), ft.colors.GREEN),
            ("自然さ", self.result_data.get("naturalness_score", 0), ft.colors.PURPLE),
            ("流暢さ", self.result_data.get("fluency_score", 0), ft.colors.ORANGE),
            ("総合", self.result_data.get("overall_score", 0), ft.colors.RED),
        ]

        bar_groups = []
        for i, (label, score, color) in enumerate(scores):
            bar_groups.append(
                ft.BarChartGroup(
                    x=i,
                    bar_rods=[
                        ft.BarChartRod(
                            from_y=0,
                            to_y=score,
                            width=40,
                            color=color,
                            tooltip=f"{label}: {score}",
                            border_radius=ft.border_radius.all(5),
                        )
                    ],
                )
            )

        chart = ft.BarChart(
            bar_groups=bar_groups,
            border=ft.border.all(1, ft.colors.GREY_200),
            bottom_axis=ft.ChartAxis(
                labels=[
                    ft.ChartAxisLabel(value=0, label=ft.Text("文法")),
                    ft.ChartAxisLabel(value=1, label=ft.Text("語彙")),
                    ft.ChartAxisLabel(value=2, label=ft.Text("自然さ")),
                    ft.ChartAxisLabel(value=3, label=ft.Text("流暢さ")),
                    ft.ChartAxisLabel(
                        value=4, label=ft.Text("総合", weight=ft.FontWeight.BOLD)
                    ),
                ],
                labels_size=40,
            ),
            left_axis=ft.ChartAxis(labels_size=40, title=ft.Text("スコア")),
            horizontal_grid_lines=ft.ChartGridLines(
                color=ft.colors.GREY_300, width=1, dash_pattern=[3, 3]
            ),
            tooltip_bgcolor=ft.colors.with_opacity(0.8, ft.colors.BLUE_GREY),
            max_y=100,
            interactive=True,
            expand=True,
        )

        return ft.Container(
            content=chart,
            width=500,
            height=300,
            padding=20,
            border=ft.border.all(1, ft.colors.GREY_300),
            border_radius=10,
            bgcolor=ft.colors.WHITE,
        )

    def _create_score_details(self) -> ft.Container:
        """スコア詳細表示を作成"""
        scores = [
            ("総合スコア", self.result_data.get("overall_score", 0), ft.colors.RED),
            ("文法", self.result_data.get("grammar_score", 0), ft.colors.BLUE),
            ("語彙", self.result_data.get("vocabulary_score", 0), ft.colors.GREEN),
            ("自然さ", self.result_data.get("naturalness_score", 0), ft.colors.PURPLE),
            ("流暢さ", self.result_data.get("fluency_score", 0), ft.colors.ORANGE),
        ]

        rows = []

        # TOEIC予測スコア表示（存在する場合）
        predicted_toeic = self.result_data.get("predicted_toeic_score")
        if predicted_toeic is not None:
            rows.append(
                ft.Container(
                    content=ft.Row(
                        [
                            ft.Text(
                                "TOEIC予測",
                                size=18,
                                weight=ft.FontWeight.BOLD,
                                width=100,
                            ),
                            ft.ProgressBar(
                                value=predicted_toeic / 990,
                                color=ft.colors.INDIGO,
                                bgcolor=ft.colors.GREY_100,
                                expand=True,
                                height=10,
                            ),
                            ft.Container(width=10),
                            ft.Text(
                                f"{predicted_toeic}",
                                size=18,
                                weight=ft.FontWeight.BOLD,
                                width=60,
                                text_align=ft.TextAlign.RIGHT,
                            ),
                        ],
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    ),
                    padding=ft.padding.only(bottom=15),
                )
            )
            rows.append(ft.Divider(height=20, color=ft.colors.GREY_300))

        for label, score, color in scores:
            rows.append(
                ft.Container(
                    content=ft.Row(
                        [
                            ft.Text(
                                label, size=18, weight=ft.FontWeight.BOLD, width=100
                            ),
                            ft.ProgressBar(
                                value=score / 100,
                                color=color,
                                bgcolor=ft.colors.GREY_100,
                                expand=True,
                                height=10,
                            ),
                            ft.Container(width=10),
                            ft.Text(
                                f"{score}/100",
                                size=18,
                                weight=ft.FontWeight.BOLD,
                                width=60,
                                text_align=ft.TextAlign.RIGHT,
                            ),
                        ],
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    ),
                    padding=ft.padding.only(bottom=15),
                )
            )

        return ft.Container(
            content=ft.Column(rows),
            width=400,
            padding=20,
            border=ft.border.all(1, ft.colors.GREY_300),
            border_radius=10,
            bgcolor=ft.colors.WHITE,
        )

    def _create_feedback_section(self) -> ft.Container:
        """フィードバック表示セクションを作成"""
        feedback_text = self.result_data.get("feedback", "フィードバックがありません。")

        return ft.Container(
            content=ft.Column(
                [
                    ft.Text(
                        "AIからのフィードバック", size=20, weight=ft.FontWeight.BOLD
                    ),
                    ft.Container(height=10),
                    ft.Container(
                        content=ft.Markdown(
                            feedback_text,
                            selectable=True,
                            extension_set=ft.MarkdownExtensionSet.GITHUB_WEB,
                        ),
                        padding=20,
                        border=ft.border.all(1, ft.colors.GREY_300),
                        border_radius=10,
                        bgcolor=ft.colors.GREY_50,
                        width=940,  # チャート(500) + スペース(40) + 詳細(400)
                    ),
                ]
            ),
            alignment=ft.alignment.center,
        )

    def _on_back_clicked(self, e: ft.ControlEvent) -> None:
        """戻るボタンがクリックされたときの処理"""
        if self.on_back_callback:
            self.on_back_callback()
