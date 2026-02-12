"""
結果画面のGUIコンポーネント
"""

import flet as ft
from typing import Callable, Any
import json
from datetime import datetime


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

    def _extract_level(self, feedback: str) -> int | None:
        """フィードバックテキストから会話レベルを抽出"""
        try:
            # "**推定会話レベル: X/10**" の形式を探す
            import re

            match = re.search(r"推定会話レベル:\s*(\d+)/10", feedback)
            if match:
                return int(match.group(1))
            return None
        except Exception:
            return None

    def _on_copy_research_data_clicked(self, e: ft.ControlEvent) -> None:
        """研究用データをクリップボードにコピー"""
        try:
            # データの抽出と整形
            data = {
                "timestamp": datetime.now().isoformat(),
                "predicted_total": self.result_data.get("predicted_total_score"),
                "listening_score": self.result_data.get("listening_score"),
                "reading_score": self.result_data.get("reading_score"),  # TOEIC予測から
                "conversation_level": self._extract_level(
                    self.result_data.get("feedback", "")
                ),
                "grammar": self.result_data.get("grammar_score"),
                "vocabulary": self.result_data.get("vocabulary_score"),
                "naturalness": self.result_data.get("naturalness_score"),
                "fluency": self.result_data.get("fluency_score"),
                "overall": self.result_data.get("overall_score"),
            }

            # JSON文字列に変換
            json_str = json.dumps(data, ensure_ascii=False)

            # クリップボードにコピー
            self.page.set_clipboard(json_str)

            # 通知を表示
            self.page.snack_bar = ft.SnackBar(
                content=ft.Text("研究用データをクリップボードにコピーしました"),
                bgcolor=ft.colors.GREEN_700,
            )
            self.page.snack_bar.open = True
            self.page.update()

        except Exception as ex:
            print(f"データコピーエラー: {ex}")
            self.page.snack_bar = ft.SnackBar(
                content=ft.Text("データのコピーに失敗しました"),
                bgcolor=ft.colors.RED_700,
            )
            self.page.snack_bar.open = True
            self.page.update()

    def build(self) -> None:
        """ウィジェットの構築"""
        self.page.clean()

        # 結果データの種類をチェック
        has_conversation = "overall_score" in self.result_data
        has_listening = "listening_results" in self.result_data

        # 両方のデータがある場合はタブで表示（総合結果として）
        if has_conversation and has_listening:
            self._build_combined_result()
        elif has_listening:
            self._build_listening_result()
        else:
            self._build_conversation_result()

    def _create_copy_data_button(self) -> ft.ElevatedButton:
        """研究用データコピーボタンを作成"""
        return ft.ElevatedButton(
            "研究用データをコピー",
            icon=ft.icons.COPY,
            on_click=self._on_copy_research_data_clicked,
            width=200,
            height=50,
            bgcolor=ft.colors.GREY_700,
            color=ft.colors.WHITE,
        )

    def _build_combined_result(self) -> None:
        """総合結果画面（タブ表示）の構築"""
        title = ft.Text(
            "総合テスト結果",
            size=32,
            weight=ft.FontWeight.BOLD,
            text_align=ft.TextAlign.CENTER,
            color=ft.colors.BLACK,
        )

        # 会話（総合）タブの内容
        conversation_content = self._create_conversation_content_container()

        # リスニングタブの内容
        listening_content = self._create_listening_content_container()

        # タブの作成
        tabs = ft.Tabs(
            selected_index=0,
            animation_duration=300,
            tabs=[
                ft.Tab(
                    text="総合スコア・会話評価",
                    content=conversation_content,
                ),
                ft.Tab(
                    text="リスニング詳細",
                    content=listening_content,
                ),
            ],
            expand=True,
        )

        # 戻るボタン
        back_button = ft.ElevatedButton(
            "メイン画面に戻る",
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
                    ft.Container(height=20),
                    tabs,
                    ft.Container(height=20),
                    ft.Row(
                        [
                            back_button,
                            ft.Container(width=20),
                            self._create_copy_data_button(),
                        ],
                        alignment=ft.MainAxisAlignment.CENTER,
                    ),
                    ft.Container(height=20),
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                expand=True,
            ),
            padding=20,
            expand=True,
            bgcolor=ft.colors.WHITE,
        )

        self.page.add(content)
        self.page.update()

    def _create_conversation_content_container(self) -> ft.Container:
        """会話（総合）結果のコンテナを作成（スクロール可能）"""
        score_chart = self._create_score_chart()
        score_details = self._create_score_details()
        feedback_section = self._create_feedback_section()

        return ft.Container(
            content=ft.Column(
                [
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
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                scroll=ft.ScrollMode.AUTO,
            ),
            padding=20,
            expand=True,
        )

    def _create_listening_content_container(self) -> ft.Container:
        """リスニング結果のコンテナを作成（スクロール可能）"""
        score = self.result_data.get("listening_score", 0)
        total = self.result_data.get("listening_question_count", 0)
        percentage = (score / total * 100) if total > 0 else 0

        score_display = ft.Container(
            content=ft.Column(
                [
                    ft.Text("リスニング正解率", size=18, color=ft.colors.GREY_700),
                    ft.Text(
                        f"{percentage:.1f}%",
                        size=48,
                        weight=ft.FontWeight.BOLD,
                        color=ft.colors.BLUE_600
                        if percentage >= 60
                        else ft.colors.RED_400,
                    ),
                    ft.Text(
                        f"{score} / {total} 問正解", size=20, weight=ft.FontWeight.BOLD
                    ),
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            padding=20,
            border=ft.border.all(1, ft.colors.GREY_300),
            border_radius=10,
            bgcolor=ft.colors.WHITE,
        )

        review_section = self._create_listening_review_section()

        return ft.Container(
            content=ft.Column(
                [
                    ft.Container(height=20),
                    score_display,
                    ft.Container(height=30),
                    ft.Text("復習・スクリプト確認", size=24, weight=ft.FontWeight.BOLD),
                    ft.Container(height=10),
                    review_section,
                    ft.Container(height=30),
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                scroll=ft.ScrollMode.AUTO,
            ),
            padding=20,
            expand=True,
        )

    def _build_conversation_result(self) -> None:
        """会話テスト結果画面の構築"""
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
            "メイン画面に戻る",
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
                    ft.Row(
                        [
                            back_button,
                            ft.Container(width=20),
                            self._create_copy_data_button(),
                        ],
                        alignment=ft.MainAxisAlignment.CENTER,
                    ),
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

    def _build_listening_result(self) -> None:
        """リスニングテスト結果画面の構築"""
        # タイトル
        title = ft.Text(
            "リスニングテスト結果",
            size=32,
            weight=ft.FontWeight.BOLD,
            text_align=ft.TextAlign.CENTER,
            color=ft.colors.BLACK,
        )

        score = self.result_data.get("listening_score", 0)
        total = self.result_data.get("listening_question_count", 0)
        percentage = (score / total * 100) if total > 0 else 0

        # スコア表示
        score_display = ft.Container(
            content=ft.Column(
                [
                    ft.Text("正解率", size=18, color=ft.colors.GREY_700),
                    ft.Text(
                        f"{percentage:.1f}%",
                        size=48,
                        weight=ft.FontWeight.BOLD,
                        color=ft.colors.BLUE_600
                        if percentage >= 60
                        else ft.colors.RED_400,
                    ),
                    ft.Text(
                        f"{score} / {total} 問正解", size=20, weight=ft.FontWeight.BOLD
                    ),
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            padding=20,
            border=ft.border.all(1, ft.colors.GREY_300),
            border_radius=10,
            bgcolor=ft.colors.WHITE,
        )

        # パッセージと問題の表示エリア
        review_section = self._create_listening_review_section()

        # 戻るボタン
        back_button = ft.ElevatedButton(
            "メイン画面に戻る",
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
                    ft.Container(height=20),
                    score_display,
                    ft.Container(height=30),
                    ft.Text("復習・スクリプト確認", size=24, weight=ft.FontWeight.BOLD),
                    ft.Container(height=10),
                    review_section,
                    ft.Container(height=30),
                    ft.Row(
                        [
                            back_button,
                            ft.Container(width=20),
                            self._create_copy_data_button(),
                        ],
                        alignment=ft.MainAxisAlignment.CENTER,
                    ),
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

    def _create_listening_review_section(self) -> ft.Container:
        """リスニングのスクリプトと問題ごとの詳細を作成"""
        passages = self.result_data.get("listening_passages", [])
        results = self.result_data.get("listening_results", [])

        # 結果をパッセージごとにグループ化
        # resultsの各アイテムには passage_index が含まれていると仮定
        results_by_passage = {}
        for res in results:
            p_idx = res.get("passage_index", 0)
            if p_idx not in results_by_passage:
                results_by_passage[p_idx] = []
            results_by_passage[p_idx].append(res)

        content_controls = []

        for i, passage_data in enumerate(passages):
            passage_text = passage_data.get("passage", "")
            passage_questions = results_by_passage.get(i, [])

            # パッセージ表示
            content_controls.append(
                ft.Container(
                    content=ft.Column(
                        [
                            ft.Text(
                                f"Passage {i + 1}",
                                size=18,
                                weight=ft.FontWeight.BOLD,
                                color=ft.colors.BLUE_800,
                            ),
                            ft.Container(height=10),
                            ft.Markdown(
                                passage_text,
                                selectable=True,
                            ),
                        ]
                    ),
                    padding=20,
                    bgcolor=ft.colors.GREY_50,
                    border_radius=10,
                    border=ft.border.all(1, ft.colors.GREY_200),
                )
            )
            content_controls.append(ft.Container(height=20))

            # このパッセージに関連する問題の表示
            for q_idx, res in enumerate(passage_questions):
                is_correct = res.get("is_correct", False)
                user_ans = res.get("user_answer", "-")
                correct_ans = res.get("correct_answer", "-")
                question_text = res.get("question", "")
                options = res.get("options", [])

                # アイコンと色設定
                status_icon = ft.icons.CHECK_CIRCLE if is_correct else ft.icons.CANCEL
                status_color = ft.colors.GREEN if is_correct else ft.colors.RED

                # 選択肢の表示文字列作成
                options_display = []
                labels = ["A", "B", "C", "D"]
                for j, opt in enumerate(options):
                    label_char = labels[j] if j < len(labels) else "?"
                    # 正解の選択肢を強調
                    is_this_correct = label_char == correct_ans
                    # ユーザーが間違えて選んだ選択肢を強調
                    is_this_wrong_choice = label_char == user_ans and not is_correct

                    opt_color = ft.colors.BLACK
                    weight = ft.FontWeight.NORMAL

                    if is_this_correct:
                        opt_color = ft.colors.GREEN_700
                        weight = ft.FontWeight.BOLD
                        opt = f"{opt} (Correct)"
                    elif is_this_wrong_choice:
                        opt_color = ft.colors.RED_700
                        opt = f"{opt} (Your Answer)"

                    options_display.append(
                        ft.Text(f"{label_char}. {opt}", color=opt_color, weight=weight)
                    )

                # 問題カード
                question_card = ft.Container(
                    content=ft.Row(
                        [
                            ft.Icon(status_icon, color=status_color, size=30),
                            ft.Container(width=15),
                            ft.Column(
                                [
                                    ft.Text(
                                        f"Q{q_idx + 1}. {question_text}",
                                        weight=ft.FontWeight.BOLD,
                                        size=16,
                                    ),
                                    ft.Container(height=5),
                                    ft.Column(options_display, spacing=2),
                                    ft.Container(height=5),
                                    ft.Text(
                                        f"正解: {correct_ans} / あなたの回答: {user_ans}",
                                        color=ft.colors.GREY_700,
                                    ),
                                ],
                                expand=True,
                            ),
                        ],
                        vertical_alignment=ft.CrossAxisAlignment.START,
                    ),
                    padding=15,
                    border=ft.border.all(
                        1, ft.colors.GREY_200 if is_correct else ft.colors.RED_100
                    ),
                    bgcolor=ft.colors.WHITE if is_correct else ft.colors.RED_50,
                    border_radius=8,
                )
                content_controls.append(question_card)
                content_controls.append(ft.Container(height=10))

            content_controls.append(ft.Divider(height=40, color=ft.colors.GREY_400))

        return ft.Container(
            content=ft.Column(content_controls),
            width=800,
        )

    def _create_score_chart(self) -> ft.Container:
        """レーダーチャート風の表示（FletにRadarChartがないので棒グラフで代用）を作成"""
        scores = [
            ("文法", self.result_data.get("grammar_score", 0), ft.colors.BLUE),
            ("語彙", self.result_data.get("vocabulary_score", 0), ft.colors.GREEN),
            ("自然さ", self.result_data.get("naturalness_score", 0), ft.colors.PURPLE),
            ("流暢さ", self.result_data.get("fluency_score", 0), ft.colors.ORANGE),
            ("会話総合", self.result_data.get("overall_score", 0), ft.colors.RED),
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
                        value=4, label=ft.Text("会話総合", weight=ft.FontWeight.BOLD)
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
            ("会話総合スコア", self.result_data.get("overall_score", 0), ft.colors.RED),
            ("文法", self.result_data.get("grammar_score", 0), ft.colors.BLUE),
            ("語彙", self.result_data.get("vocabulary_score", 0), ft.colors.GREEN),
            ("自然さ", self.result_data.get("naturalness_score", 0), ft.colors.PURPLE),
            ("流暢さ", self.result_data.get("fluency_score", 0), ft.colors.ORANGE),
        ]

        rows = []

        # TOEIC予測スコア表示（存在する場合）
        predicted_toeic = self.result_data.get("predicted_total_score")
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
