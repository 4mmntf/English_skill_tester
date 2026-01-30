"""
会話画面のGUIコンポーネント
"""
import flet as ft
import time
import threading
import random
import json
import re
import traceback
from typing import Any
from datetime import datetime
from pathlib import Path
import numpy as np
from numpy.typing import NDArray
import sounddevice as sd
import asyncio
import aiofiles
from pydub import AudioSegment
from app.services.audio_service import AudioService
from app.services.api_check_service import APICheckService
from app.services.storage_service import LocalStorageService
from app.services.realtime_service import RealtimeService
from app.services.evaluation_service import EvaluationService


class ConversationWindow:
    """会話画面のウィンドウクラス"""
    
    def __init__(self, page: ft.Page) -> None:
        """
        初期化処理
        
        Args:
            page: Fletのページオブジェクト
        """
        self.page = page
        
        # サービス初期化
        self.audio_service = AudioService()
        self.api_check_service = APICheckService()
        self.storage_service = LocalStorageService()
        self.realtime_service: RealtimeService | None = None
        self.evaluation_service: EvaluationService = EvaluationService()
        
        # テスト項目の定義（メイン画面を最初に追加）
        self.test_items: list[dict[str, str]] = [
            {"id": "main", "name": "メイン画面", "description": "APIチェックとマイク・スピーカーのテスト"},
            {"id": "pronunciation", "name": "発音テスト", "description": "単語や文章の発音を評価します"},
            {"id": "conversation", "name": "会話テスト", "description": "リアルタイム会話を評価します"},
            {"id": "listening", "name": "リスニングテスト", "description": "聞き取り能力を評価します"},
            {"id": "grammar", "name": "文法テスト", "description": "文法の正確性を評価します"},
        ]
        
        # 録音状態（メイン画面用）
        self.is_recording: bool = False
        self.recorded_audio: list[float] | None = None
        
        # リアルタイム波形表示用（メイン画面用）
        self.mic_waveform_buffer: list[float] = []
        self.speaker_waveform_buffer: list[float] = []
        self.max_buffer_size: int = 200
        self.last_update_time: float = 0.0
        self.update_interval: float = 0.05
        
        # メイン画面用UIコンポーネント
        self.mic_chart: ft.LineChart | None = None
        self.speaker_chart: ft.LineChart | None = None
        self.api_status_texts: dict[str, ft.Text] = {}
        self.test_button: ft.ElevatedButton | None = None
        self.status_text: ft.Text | None = None
        
        # タイマー関連（全体の実行時間）
        self.overall_start_time: datetime | None = None
        self.overall_timer_running: bool = False
        self.overall_timer_text: ft.Text | None = None
        self.overall_timer_thread: threading.Thread | None = None
        
        # 各タブのタイマー関連
        self.tab_timers: dict[str, dict[str, Any]] = {}  # test_id -> {start_time, running, text, thread, final_time}
        
        # テスト状態
        self.test_initialized: bool = False  # テストが初期化済みかどうか
        self.test_status_text: ft.Text | None = None  # テスト状態表示
        
        # 現在のテスト項目
        self.current_test_id: str | None = None
        
        # UIコンポーネント
        self.tabs: ft.Tabs | None = None
        self.tab_status_texts: dict[str, ft.Text] = {}
        self.tab_start_buttons: dict[str, ft.ElevatedButton] = {}  # 各タブの「テストを開始する」ボタン
        self.tab_controls: list[ft.Tab] = []  # タブコントロールのリスト（無効化用）
        self.cancel_test_button: ft.ElevatedButton | None = None  # 「テストを中断する」ボタン
        self.pause_test_button: ft.ElevatedButton | None = None  # 「テストを一時停止する」/「テストを再開する」ボタン
        self.test_running: bool = False  # テストが実行中かどうか
        self.test_paused: bool = False  # テストが一時停止中かどうか
        self.global_status_text: ft.Text | None = None  # 一時停止・中断ボタンの上に表示するステータステキスト
        
        # 会話テスト用のコンポーネント
        self.roleplay_dropdown: ft.Dropdown | None = None  # ロールプレイ選択ドロップダウン
        self.teacher_image: ft.Image | None = None  # 講師の3Dモデル画像
        self.student_waveform_chart: ft.LineChart | None = None  # 学生用の音声波形
        self.student_waveform_buffer: list[float] = []  # 学生用波形バッファ
        self.conversation_session_duration_minutes: int = 1  # 会話セッションの時間（分） - 開発用に調整可能
        self.conversation_running: bool = False  # 会話テスト実行中フラグ
        self.ai_audio_playing: bool = False  # 音声再生中フラグ
        self.ai_audio_stream: sd.OutputStream | None = None  # 音声ストリーム（連続再生用）
        self.ai_audio_buffer_queue: list[NDArray[np.floating]] = []  # AI音声バッファキュー（再生用）
        self.ai_audio_buffer_queue_lock: threading.Lock = threading.Lock()  # バッファキューアクセス用ロック
        self.audio_threshold: float = 0.002  # 音声検出の閾値（ノイズを除外しつつ、音声を確実に検出）
        self.audio_send_count: int = 0  # 音声送信回数（デバッグ用）
        self.last_audio_send_time: float = 0.0  # 最後に音声を送信した時刻（デバッグ用）
        
        # 会話履歴の記録
        self.conversation_history: list[dict[str, str]] = []  # 会話履歴 [{"role": "ai" or "student", "text": "..."}]
        self.evaluation_mode: bool = False  # 評価モード（評価依頼中の返答を評価結果として扱う）
        self.evaluation_request_count: int = 0  # 評価依頼回数（重複評価を防ぐ）
        
        # 評価スコアの履歴（折れ線グラフ用）
        self.evaluation_scores_history: list[dict[str, float]] = []  # [{"grammar": 80, "vocabulary": 75, "naturalness": 70, "fluency": 85, "overall": 77.5}, ...]
        self.score_chart: ft.LineChart | None = None  # スコア折れ線グラフ
        self.evaluation_feedback_text: ft.Text = ft.Text(
            "",
            size=18,
            color=ft.Colors.BLACK,
            text_align=ft.TextAlign.CENTER,
            weight=ft.FontWeight.BOLD,
        )  # 評価スコアと講評を表示するテキスト（画面下）
        
        # 音声録音用のバッファ（保存用）
        self.ai_audio_recording_buffer: list[NDArray[np.floating]] = []  # AI音声録音バッファ
        self.ai_audio_recording_lock: threading.Lock = threading.Lock()  # 録音バッファアクセス用ロック
        self.student_audio_recording_buffer: list[NDArray[np.floating]] = []  # 学生音声録音バッファ
        self.student_audio_recording_lock: threading.Lock = threading.Lock()  # 録音バッファアクセス用ロック
        self.student_recording_thread: threading.Thread | None = None  # 学生音声録音スレッド
        self.student_recording_stream: sd.InputStream | None = None  # 学生音声録音ストリーム
        
        # 保存場所の設定（デフォルトはDesktop）
        self.save_directory: Path = Path.home() / "Desktop"
        self.save_directory_picker: ft.FilePicker | None = None  # 保存場所選択用のFilePicker
        self.save_directory_text: ft.Text | None = None  # 保存場所表示用のテキスト
        self.save_directory_button: ft.ElevatedButton | None = None  # 保存場所選択ボタン

    def build(self) -> None:
        """ウィジェットの構築"""
        # テスト状態の確認
        has_progress = self.storage_service.has_test_progress()
        self.test_initialized = not has_progress
        
        # タイトル
        title = ft.Text(
            "英会話能力測定",
            size=28,
            weight=ft.FontWeight.BOLD,
            text_align=ft.TextAlign.CENTER,
            color=ft.Colors.BLACK
        )
        
        # タブの作成
        self.tabs = self._create_tabs()
        
        # テスト状態表示（右上の最も高いところ）
        status_label = "テストの状態：初期化済み" if self.test_initialized else "テストの状態：継続中"
        self.test_status_text = ft.Text(
            status_label,
            size=16,
            color=ft.Colors.BLACK,
            weight=ft.FontWeight.BOLD
        )
        
        test_status_container = ft.Container(
            content=self.test_status_text,
            padding=10,
            bgcolor=ft.Colors.WHITE,
            border=ft.border.all(1, ft.Colors.GREY_400),
            border_radius=5,
        )
        
        # 全体の実行時間タイマー（右上、テスト状態の下）
        self.overall_timer_text = ft.Text(
            "実行時間: 00:00:00",
            size=16,
            color=ft.Colors.BLACK,
            weight=ft.FontWeight.BOLD
        )
        
        overall_timer_container = ft.Container(
            content=self.overall_timer_text,
            padding=10,
            bgcolor=ft.Colors.WHITE,
            border=ft.border.all(1, ft.Colors.GREY_400),
            border_radius=5,
        )
        
        # 「テストを一時停止する」/「テストを再開する」ボタン（画面下部の中央左）
        self.pause_test_button = ft.ElevatedButton(
            "テストを一時停止する",
            on_click=self._on_pause_test_clicked,
            width=250,
            height=50,
            bgcolor=ft.Colors.BLUE_400,
            color=ft.Colors.WHITE,
            visible=False,  # 初期状態では非表示
        )
        
        # 「テストを中断する」ボタン（画面下部の中央右）
        self.cancel_test_button = ft.ElevatedButton(
            "テストを中断する",
            on_click=self._on_cancel_test_clicked,
            width=250,
            height=50,
            bgcolor=ft.Colors.ORANGE_400,
            color=ft.Colors.WHITE,
            visible=False,  # 初期状態では非表示
        )
        
        # ステータステキスト用のプレースホルダー（会話テストのstatus_textを参照）
        # 実際のstatus_textは各タブで作成されるが、ここでは一時停止・中断ボタンの上に表示するための参照を保持
        self.global_status_text = ft.Text(
            "",
            size=14,
            color=ft.Colors.GREY_700,
            text_align=ft.TextAlign.CENTER,
        )
        
        # ボタンを横並びに配置（ステータステキストを上に配置）
        buttons_container = ft.Container(
            content=ft.Column(
                [
                    # ステータステキスト（会話テストのstatus_textを参照、初期状態では非表示）
                    self.global_status_text,
                    ft.Container(height=10),
                    # 一時停止・中断ボタン
                    ft.Row(
                        [
                            self.pause_test_button,
                            ft.Container(width=20),  # ボタン間のスペース
                            self.cancel_test_button,
                        ],
                        alignment=ft.MainAxisAlignment.CENTER,
                    ),
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=0,
            ),
            padding=10,
        )
        
        # メインコンテンツ
        main_content = ft.Container(
            content=ft.Column(
                [
                    ft.Container(height=20),
                    title,
                    ft.Container(height=20),
                    self.tabs,
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=0,
                expand=True,
            ),
            padding=40,
            expand=True,
        )
        
        # レイアウト（Stackで右上にテスト状態とタイマー、下部中央に中断ボタンを配置）
        self.page.add(
            ft.Stack(
                [
                    main_content,
                    ft.Container(
                        content=ft.Column(
                            [
                                test_status_container,
                                ft.Container(height=10),
                                overall_timer_container,
                            ],
                            spacing=0,
                        ),
                        right=20,
                        top=20,
                    ),
                    ft.Container(
                        content=buttons_container,
                        bottom=20,
                        left=0,
                        right=0,
                        alignment=ft.alignment.center,
                    ),
                ],
                expand=True,
            )
        )
        
        self.page.update()

    def _create_tabs(self) -> ft.Tabs:
        """タブコンポーネントの作成"""
        self.tab_controls = []
        
        for test_item in self.test_items:
            tab_content = self._create_tab_content(test_item)
            tab = ft.Tab(
                text=test_item["name"],
                content=tab_content,
            )
            # 元のテキストを保存（動的属性として追加）
            setattr(tab, "_original_text", test_item["name"])
            setattr(tab, "_test_id", test_item["id"])
            self.tab_controls.append(tab)
        
        tabs = ft.Tabs(
            tabs=self.tab_controls,
            selected_index=0,
            on_change=self._on_tab_changed,
            expand=True,
            unselected_label_color=ft.Colors.BLACK,  # 通常時は黒
        )
        
        # メイン画面タブが選択されている場合、APIチェックとリアルタイム監視を開始
        if len(self.test_items) > 0 and self.test_items[0]["id"] == "main":
            self._initialize_main_tab()
        
        return tabs
    
    def _initialize_main_tab(self) -> None:
        """メイン画面タブの初期化"""
        # APIチェック
        self._check_apis()
        # リアルタイム波形表示を開始
        self._start_realtime_monitoring()
    
    def _check_apis(self) -> None:
        """APIの状態をチェック"""
        api_results = self.api_check_service.check_all_apis()
        
        for api_result in api_results:
            if api_result['name'] in self.api_status_texts:
                status_text = self.api_status_texts[api_result['name']]
                status_text.value = f"{api_result['name']}の状態：{api_result['status']}"
                
                # 状態に応じて色を変更
                if api_result['status'] == "利用可能":
                    status_text.color = ft.Colors.GREEN
                elif api_result['status'] == "エラー":
                    status_text.color = ft.Colors.RED
                else:
                    status_text.color = ft.Colors.ORANGE
        
        self.page.update()
    
    def _start_realtime_monitoring(self) -> None:
        """リアルタイム波形監視を開始"""
        # マイクの監視を開始
        self.audio_service.start_mic_monitoring(self._on_mic_data_received)
    
    def _on_mic_data_received(self, audio_data: list[float]) -> None:
        """マイクデータ受信時のコールバック"""
        try:
            # RMS値（実効値）を計算して波形の強度を取得
            if len(audio_data) > 0:
                np_data: NDArray[np.floating] = np.array(audio_data, dtype=np.float32)
                rms: float = float(np.sqrt(np.mean(np_data ** 2)))
                # ピーク値も取得
                peak: float = float(np.max(np.abs(np_data)))
                # より視覚的に分かりやすくするため、RMSとピークの平均を使用
                value = (rms + peak) / 2.0
            else:
                value = 0.0
            
            # バッファに追加
            self.mic_waveform_buffer.append(value)
            if len(self.mic_waveform_buffer) > self.max_buffer_size:
                self.mic_waveform_buffer.pop(0)
            
            # 更新頻度を制限（一定間隔でのみ更新）
            current_time = time.time()
            if current_time - self.last_update_time >= self.update_interval:
                self.last_update_time = current_time
                # 波形を更新（Fletでは直接page.update()を呼び出せる）
                self._update_realtime_mic_waveform()
        except Exception as e:
            print(f"マイクデータ処理エラー: {str(e)}")
    
    def _update_realtime_mic_waveform(self) -> None:
        """リアルタイムマイク波形の更新"""
        if not self.mic_chart:
            return
        
        try:
            # バッファからデータポイントを生成
            data_points: list[ft.LineChartDataPoint] = []
            buffer_size = len(self.mic_waveform_buffer)
            
            if buffer_size > 0:
                # バッファのデータをそのまま使用（時系列データとして表示）
                for i, value in enumerate(self.mic_waveform_buffer):
                    # 値の範囲を0.0～1.0に正規化（実際のRMS値は小さいので拡大）
                    normalized_value = max(0.0, min(1.0, value * 10.0))  # 10倍に拡大して視認性を向上
                    data_points.append(ft.LineChartDataPoint(i, normalized_value))
            else:
                # データがない場合はゼロで埋める
                data_points = [ft.LineChartDataPoint(i, 0.0) for i in range(self.max_buffer_size)]
            
            # チャートのX軸範囲を調整
            self.mic_chart.max_x = max(self.max_buffer_size, buffer_size)
            
            # データポイントを更新
            if self.mic_chart.data_series and len(self.mic_chart.data_series) > 0:
                self.mic_chart.data_series[0].data_points = data_points
                self.page.update()
        except Exception as e:
            print(f"リアルタイムマイク波形更新エラー: {str(e)}")
    
    def _on_test_button_clicked(self, e: ft.ControlEvent) -> None:
        """テストボタンがクリックされたときの処理"""
        if self.is_recording:
            return
        
        def test_audio():
            """録音→再生のテスト処理"""
            try:
                self.is_recording = True
                if self.status_text:
                    self.status_text.value = "録音中...「Hello」と発話してください（3秒間）"
                    self.status_text.color = ft.Colors.BLUE
                if self.test_button:
                    self.test_button.disabled = True
                self.page.update()
                
                # 録音（3秒間）
                audio_data = self.audio_service.record_audio(duration=3.0)
                
                if len(audio_data) > 0:
                    # 録音波形を表示（numpy配列をリストに変換）
                    audio_list = audio_data.tolist() if isinstance(audio_data, np.ndarray) else audio_data
                    self._update_mic_waveform(audio_list)
                    
                    if self.status_text:
                        self.status_text.value = "再生中..."
                        self.status_text.color = ft.Colors.GREEN
                    self.page.update()
                    
                    # 再生（音量ゲイン10倍で再生）
                    amplified_audio_data = self.audio_service.play_audio(audio_data, volume_gain=10.0)
                    
                    # 再生波形を表示（増幅後のデータを使用）
                    if amplified_audio_data is not None:
                        audio_list = amplified_audio_data.tolist() if isinstance(amplified_audio_data, np.ndarray) else amplified_audio_data
                        self._update_speaker_waveform(audio_list)
                    
                    if self.status_text:
                        self.status_text.value = "テスト完了！マイクとスピーカーが正常に動作しています。"
                        self.status_text.color = ft.Colors.GREEN
                else:
                    if self.status_text:
                        self.status_text.value = "録音に失敗しました。マイクの接続を確認してください。"
                        self.status_text.color = ft.Colors.RED
                
                if self.test_button:
                    self.test_button.disabled = False
                self.page.update()
                
            except Exception as ex:
                print(f"テストエラー: {str(ex)}")
                if self.status_text:
                    self.status_text.value = f"エラーが発生しました: {str(ex)}"
                    self.status_text.color = ft.Colors.RED
                if self.test_button:
                    self.test_button.disabled = False
                self.page.update()
            finally:
                self.is_recording = False
        
        # 別スレッドで実行
        test_thread = threading.Thread(target=test_audio, daemon=True)
        test_thread.start()
    
    def _update_mic_waveform(self, audio_data: list[float] | None) -> None:
        """マイク波形の更新"""
        if not self.mic_chart or not audio_data:
            return
        
        try:
            # データをサンプリングして表示
            data_length = len(audio_data)
            if data_length > 0:
                # より多くのポイントを表示（200ポイント）
                step = max(1, data_length // self.max_buffer_size)
                mic_points: list[ft.LineChartDataPoint] = []
                for i in range(0, min(data_length, self.max_buffer_size * step), step):
                    x = i // step
                    # 振幅の絶対値を使用（0から1の範囲）
                    y = abs(float(audio_data[i])) if i < data_length else 0.0
                    mic_points.append(ft.LineChartDataPoint(x, y))
                
                if not mic_points:
                    mic_points = [ft.LineChartDataPoint(i, 0.0) for i in range(self.max_buffer_size)]
                
                # X軸範囲を調整
                self.mic_chart.max_x = max(self.max_buffer_size, len(mic_points))
                
                if self.mic_chart.data_series and len(self.mic_chart.data_series) > 0:
                    self.mic_chart.data_series[0].data_points = mic_points
                    self.page.update()
        except Exception as e:
            print(f"マイク波形更新エラー: {str(e)}")
    
    def _update_speaker_waveform(self, audio_data: list[float] | None) -> None:
        """スピーカー波形の更新"""
        if not self.speaker_chart or not audio_data:
            return
        
        try:
            # データをサンプリングして表示
            data_length = len(audio_data)
            if data_length > 0:
                step = max(1, data_length // self.max_buffer_size)
                speaker_points: list[ft.LineChartDataPoint] = []
                for i in range(0, min(data_length, self.max_buffer_size * step), step):
                    x = i // step
                    y = abs(float(audio_data[i])) if i < data_length else 0.0
                    speaker_points.append(ft.LineChartDataPoint(x, y))
                
                if not speaker_points:
                    speaker_points = [ft.LineChartDataPoint(i, 0.0) for i in range(self.max_buffer_size)]
                
                # X軸範囲を調整
                self.speaker_chart.max_x = max(self.max_buffer_size, len(speaker_points))
                
                if self.speaker_chart.data_series and len(self.speaker_chart.data_series) > 0:
                    self.speaker_chart.data_series[0].data_points = speaker_points
                    self.page.update()
        except Exception as e:
            print(f"スピーカー波形更新エラー: {str(e)}")

    def _create_tab_content(self, test_item: dict[str, str]) -> ft.Container:
        """タブのコンテンツを作成"""
        # メイン画面の場合は特別なコンテンツを表示
        if test_item["id"] == "main":
            return self._create_main_tab_content()
        
        # 会話テストの場合は特別なコンテンツを表示
        if test_item["id"] == "conversation":
            return self._create_conversation_test_content()
        
        if test_item["id"] == "listening":
            # リスニングテストタブのコンテンツを作成
            return self._create_listening_test_content()
        
        # その他のテスト項目
        test_id = test_item["id"]
        
        # タブ内のタイマー（右上、全体の実行時間のすぐ下）
        tab_timer_text = ft.Text(
            "テスト時間: 00:00:00",
            size=14,
            color=ft.Colors.BLACK,
            weight=ft.FontWeight.BOLD
        )
        
        tab_timer_container = ft.Container(
            content=tab_timer_text,
            padding=8,
            bgcolor=ft.Colors.WHITE,
            border=ft.border.all(1, ft.Colors.GREY_400),
            border_radius=5,
        )
        
        # タブ内タイマーを初期化
        self.tab_timers[test_id] = {
            "start_time": None,
            "running": False,
            "text": tab_timer_text,
            "thread": None,
            "final_time": None,
        }
        
        description = ft.Text(
            test_item["description"],
            size=16,
            color=ft.Colors.BLACK,
            text_align=ft.TextAlign.CENTER,
        )
        
        status_text = ft.Text(
            "「テストを開始する」ボタンをクリックしてテストを開始してください",
            size=14,
            color=ft.Colors.GREY_700,
            text_align=ft.TextAlign.CENTER,
        )
        
        # ステータステキストを保存（後で更新するため）
        self.tab_status_texts[test_id] = status_text
        
        # 「テストを開始する」ボタン
        start_button = ft.ElevatedButton(
            "テストを開始する",
            on_click=lambda e, tid=test_id: self._on_test_start_button_clicked(tid),
            width=250,
            height=45,
        )
        
        self.tab_start_buttons[test_id] = start_button
        
        # テスト履歴を読み込む
        progress = self.storage_service.load_test_progress(test_id)
        if progress:
            # 履歴がある場合は、タイマーに最終時間を設定
            if "final_time" in progress:
                final_time_str = progress["final_time"]
                tab_timer_text.value = f"テスト時間: {final_time_str}"
                self.tab_timers[test_id]["final_time"] = final_time_str
                status_text.value = "テスト履歴を読み込みました。再開するには「テストを開始する」ボタンをクリックしてください。"
                status_text.color = ft.Colors.BLUE
        
        content = ft.Container(
            content=ft.Stack(
                [
                    ft.Column(
                        [
                            ft.Container(height=40),
                            description,
                            ft.Container(height=20),
                            status_text,
                            ft.Container(height=20),
                            ft.Row([start_button], alignment=ft.MainAxisAlignment.CENTER),
                            ft.Container(height=40),
                        ],
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        alignment=ft.MainAxisAlignment.CENTER,
                    ),
                    ft.Container(
                        content=tab_timer_container,
                        right=20,
                        top=20,
                    ),
                ],
                expand=True,
            ),
            padding=40,
            expand=True,
        )
        
        return content
    
    def _create_conversation_test_content(self) -> ft.Container:
        """会話テストタブのコンテンツを作成"""
        test_id = "conversation"
        
        # タブ内のタイマー（右上、全体の実行時間のすぐ下）
        tab_timer_text = ft.Text(
            "テスト時間: 00:00:00",
            size=14,
            color=ft.Colors.BLACK,
            weight=ft.FontWeight.BOLD
        )
        
        tab_timer_container = ft.Container(
            content=tab_timer_text,
            padding=8,
            bgcolor=ft.Colors.WHITE,
            border=ft.border.all(1, ft.Colors.GREY_400),
            border_radius=5,
        )
        
        # タブ内タイマーを初期化
        self.tab_timers[test_id] = {
            "start_time": None,
            "running": False,
            "text": tab_timer_text,
            "thread": None,
            "final_time": None,
        }
        
        # ロールプレイ選択ドロップダウン
        roleplay_options = [
            ft.dropdown.Option("teacher", "英会話講師との会話"),
            ft.dropdown.Option("directions", "街中での道案内 (NotImplemented)"),
            ft.dropdown.Option("university", "留学先の大学での教員との会話 (NotImplemented)"),
            ft.dropdown.Option("introduction", "初対面の外国人への自己紹介 (NotImplemented)"),
        ]
        
        self.roleplay_dropdown = ft.Dropdown(
            label="ロールプレイを選択",
            options=roleplay_options,
            value="teacher",  # デフォルトは「英会話講師との会話」
            width=400,
            disabled=False,
            on_change=self._on_roleplay_selected,
        )
        
        # 講師の3Dモデル画像（中央に配置、できるだけ大きく表示）
        teacher_image_url = "https://3.bp.blogspot.com/-BCYMn-GZ8JA/VwdGSezqOTI/AAAAAAAA5mE/yfXpXdzcRZg7jPu0fe2v-y0dKfeQRc89g/w1200-h630-p-k-no-nu/teacher_english_woman.png"
        self.teacher_image = ft.Image(
            src=teacher_image_url,
            width=800,  # 画像を大きくする
            height=600,  # 画像を大きくする
            fit=ft.ImageFit.CONTAIN,  # アスペクト比を保ちながら大きく表示
        )
        
        # 学生用の音声波形チャート
        self.student_waveform_chart = ft.LineChart(
            data_series=[
                ft.LineChartData(
                    data_points=[],
                    stroke_width=2,
                    color=ft.Colors.ORANGE,
                    below_line_bgcolor=ft.Colors.ORANGE_100,
                )
            ],
            border=ft.border.Border(
                bottom=ft.BorderSide(2, ft.Colors.with_opacity(0.5, ft.Colors.ON_SURFACE)),
                left=ft.BorderSide(2, ft.Colors.with_opacity(0.5, ft.Colors.ON_SURFACE)),
                top=ft.BorderSide(2, ft.Colors.with_opacity(0.5, ft.Colors.ON_SURFACE)),
                right=ft.BorderSide(2, ft.Colors.with_opacity(0.5, ft.Colors.ON_SURFACE)),
            ),
            left_axis=ft.ChartAxis(labels_size=40),
            bottom_axis=ft.ChartAxis(labels_size=40),
            tooltip_bgcolor=ft.Colors.with_opacity(0.8, ft.Colors.BLUE_GREY),
            min_y=0.0,
            max_y=1.0,
            min_x=0,
            max_x=self.max_buffer_size,
            height=100,
            width=400,
        )
        
        # ステータステキスト
        status_text = ft.Text(
            "「テストを開始する」ボタンをクリックしてテストを開始してください",
            size=14,
            color=ft.Colors.GREY_700,
            text_align=ft.TextAlign.CENTER,
        )
        
        # ステータステキストを保存
        self.tab_status_texts[test_id] = status_text
        
        # 「テストを開始する」ボタン
        start_button = ft.ElevatedButton(
            "テストを開始する",
            on_click=lambda e, tid=test_id: self._on_test_start_button_clicked(tid),
            width=250,
            height=45,
        )
        
        self.tab_start_buttons[test_id] = start_button
        
        # テスト履歴を読み込む
        progress = self.storage_service.load_test_progress(test_id)
        if progress:
            if "final_time" in progress:
                final_time_str = progress["final_time"]
                tab_timer_text.value = f"テスト時間: {final_time_str}"
                self.tab_timers[test_id]["final_time"] = final_time_str
                status_text.value = "テスト履歴を読み込みました。再開するには「テストを開始する」ボタンをクリックしてください。"
                status_text.color = ft.Colors.BLUE
                # 会話テストの場合、グローバルステータステキストも更新
                if test_id == "conversation" and self.global_status_text:
                    self.global_status_text.value = status_text.value
                    self.global_status_text.color = status_text.color
        else:
            # 会話テストの場合、初期状態でもグローバルステータステキストを更新
            if test_id == "conversation" and self.global_status_text:
                self.global_status_text.value = status_text.value
                self.global_status_text.color = status_text.color
        
        # 波形バッファを初期化
        self.student_waveform_buffer = []
        
        # 評価スコアの折れ線グラフを作成
        self.score_chart = ft.LineChart(
            data_series=[
                ft.LineChartData(
                    data_points=[],
                    stroke_width=2,
                    color=ft.Colors.BLUE,
                    below_line_bgcolor=ft.Colors.BLUE_100,
                ),
                ft.LineChartData(
                    data_points=[],
                    stroke_width=2,
                    color=ft.Colors.GREEN,
                    below_line_bgcolor=ft.Colors.GREEN_100,
                ),
                ft.LineChartData(
                    data_points=[],
                    stroke_width=2,
                    color=ft.Colors.PURPLE,
                    below_line_bgcolor=ft.Colors.PURPLE_100,
                ),
                ft.LineChartData(
                    data_points=[],
                    stroke_width=2,
                    color=ft.Colors.ORANGE,
                    below_line_bgcolor=ft.Colors.ORANGE_100,
                ),
                ft.LineChartData(
                    data_points=[],
                    stroke_width=3,
                    color=ft.Colors.RED,
                    below_line_bgcolor=ft.Colors.RED_100,
                ),
            ],
            border=ft.border.Border(
                bottom=ft.BorderSide(2, ft.Colors.with_opacity(0.5, ft.Colors.ON_SURFACE)),
                left=ft.BorderSide(2, ft.Colors.with_opacity(0.5, ft.Colors.ON_SURFACE)),
                top=ft.BorderSide(2, ft.Colors.with_opacity(0.5, ft.Colors.ON_SURFACE)),
                right=ft.BorderSide(2, ft.Colors.with_opacity(0.5, ft.Colors.ON_SURFACE)),
            ),
            left_axis=ft.ChartAxis(labels_size=40),
            bottom_axis=ft.ChartAxis(labels_size=40),
            tooltip_bgcolor=ft.Colors.with_opacity(0.8, ft.Colors.BLUE_GREY),
            min_y=0.0,
            max_y=100.0,
            min_x=0,
            max_x=10,  # 最大10回の評価を表示
            height=150,
            width=400,
        )
        
        # 評価スコア履歴をリセット
        self.evaluation_scores_history = []
        
        content = ft.Container(
            content=ft.Row(
                [
                    # 左側：会話テストの要素を縦に並べる
                    ft.Column(
                        [
                            ft.Container(height=20),
                            ft.Text(
                                "ロールプレイを選択",
                                size=16,
                                weight=ft.FontWeight.BOLD,
                                text_align=ft.TextAlign.LEFT,
                                color=ft.Colors.BLACK
                            ),
                            ft.Container(height=10),
                            self.roleplay_dropdown,
                            ft.Container(height=10),
                            # 「テストを開始する」ボタンを「ロールプレイを選択」のすぐ下に配置
                            start_button,
                            ft.Container(height=20),
                            # テスト時間
                            tab_timer_container,
                            ft.Container(height=20),
                            # 学生の波形
                            ft.Text("学生（あなた）", size=16, weight=ft.FontWeight.BOLD, color=ft.Colors.ORANGE),
                            ft.Container(height=10),
                            self.student_waveform_chart,
                            ft.Container(height=20),
                            # 評価スコア
                            ft.Text("評価スコア", size=16, weight=ft.FontWeight.BOLD, color=ft.Colors.BLACK),
                            ft.Container(height=10),
                            self.score_chart,
                            ft.Container(height=40),
                        ],
                        horizontal_alignment=ft.CrossAxisAlignment.START,
                        alignment=ft.MainAxisAlignment.START,
                        scroll=ft.ScrollMode.AUTO,
                        expand=True,
                    ),
                    # 右側：講師の画像（中央に配置）
                    ft.Container(
                        content=self.teacher_image,
                        alignment=ft.alignment.center,
                        expand=True,
                    ),
                ],
                expand=True,
                spacing=40,
            ),
            padding=40,
            expand=True,
        )
        
        return content
    
    def _on_roleplay_selected(self, e: ft.ControlEvent) -> None:
        """ロールプレイが選択されたときの処理"""
        if not self.roleplay_dropdown:
            return
        
        selected_value = self.roleplay_dropdown.value
        
        # 「英会話講師との会話」が選択された場合のみ有効
        if selected_value == "teacher":
            # 講師の画像を表示（既に表示されている）
            if self.teacher_image:
                self.teacher_image.visible = True
        else:
            # 未実装のロールプレイの場合は画像を非表示
            if self.teacher_image:
                self.teacher_image.visible = False
        
        self.page.update()
    
    def _create_main_tab_content(self) -> ft.Container:
        """メイン画面タブのコンテンツを作成"""
        # タイトル
        title = ft.Text(
            "英会話能力測定AIアプリ",
            size=32,
            weight=ft.FontWeight.BOLD,
            text_align=ft.TextAlign.CENTER,
            color=ft.Colors.BLACK
        )
        
        # 説明文
        description = ft.Text(
            "AIとリアルタイムで英会話を行い、あなたの英会話能力を測定します。\n"
            "発音、文法、流暢さなど、総合的な評価を提供します。",
            size=16,
            text_align=ft.TextAlign.CENTER,
            color=ft.Colors.BLACK
        )
        
        # 「テストを初めから実行するために，データを初期化する」ボタン
        reset_button = ft.ElevatedButton(
            "テストを初めから実行するために，データを初期化する",
            on_click=self._on_reset_tests_clicked,
            width=400,
            height=50,
            bgcolor=ft.Colors.RED_400,
            color=ft.Colors.WHITE,
        )
        
        # APIチェックセクション
        api_section = self._create_api_section()
        
        # マイクとスピーカーのチェックセクション
        audio_section = self._create_audio_section()
        
        # 保存場所選択セクション
        save_location_section = self._create_save_location_section()
        
        content = ft.Container(
            content=ft.Column(
                [
                    ft.Container(height=20),
                    title,
                    ft.Container(height=10),
                    description,
                    ft.Container(height=20),
                    ft.Row([reset_button], alignment=ft.MainAxisAlignment.CENTER),
                    ft.Container(height=20),
                    # LLM APIチェックとファイル保存場所を横並びに配置
                    ft.Row(
                        [
                            api_section,
                            save_location_section,
                        ],
                        alignment=ft.MainAxisAlignment.CENTER,
                        spacing=20,
                    ),
                    ft.Container(height=20),
                    audio_section,
                    ft.Container(height=20),
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=0,
                scroll=ft.ScrollMode.AUTO,
            ),
            padding=40,
            expand=True,
        )
        
        return content
    
    def _create_save_location_section(self) -> ft.Container:
        """保存場所選択セクションの作成"""
        # FilePickerを作成（ディレクトリ選択用）
        self.save_directory_picker = ft.FilePicker(
            on_result=self._on_save_directory_selected,
        )
        self.page.overlay.append(self.save_directory_picker)
        
        # 保存場所表示用のテキスト
        self.save_directory_text = ft.Text(
            f"保存場所: {str(self.save_directory)}",
            size=14,
            color=ft.Colors.BLACK,
            text_align=ft.TextAlign.CENTER,
        )
        
        # 保存場所選択ボタン
        self.save_directory_button = ft.ElevatedButton(
            "保存場所を選択",
            on_click=self._on_select_save_directory_clicked,
            width=200,
            height=40,
            bgcolor=ft.Colors.BLUE_400,
            color=ft.Colors.WHITE,
        )
        
        return ft.Container(
            content=ft.Column(
                [
                    ft.Text(
                        "ファイル保存場所",
                        size=20,
                        weight=ft.FontWeight.BOLD,
                        text_align=ft.TextAlign.CENTER,
                        color=ft.Colors.BLACK
                    ),
                    ft.Container(height=10),
                    self.save_directory_text,
                    ft.Container(height=10),
                    ft.Row([self.save_directory_button], alignment=ft.MainAxisAlignment.CENTER),
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            padding=20,
            border=ft.border.all(1, ft.Colors.GREY_400),
            border_radius=10,
            width=400,
        )
    
    def _on_select_save_directory_clicked(self, e: ft.ControlEvent) -> None:
        """保存場所選択ボタンがクリックされたときの処理"""
        if self.save_directory_picker:
            # ディレクトリ選択ダイアログを開く
            self.save_directory_picker.get_directory_path()
    
    def _on_save_directory_selected(self, e: ft.FilePickerResultEvent) -> None:
        """保存場所が選択されたときの処理"""
        if e.path:
            try:
                selected_path = Path(e.path)
                if selected_path.is_dir():
                    self.save_directory = selected_path
                    if self.save_directory_text:
                        self.save_directory_text.value = f"保存場所: {str(self.save_directory)}"
                        self.page.update()
                else:
                    print(f"選択されたパスはディレクトリではありません: {e.path}")
            except Exception as ex:
                print(f"保存場所の設定エラー: {str(ex)}")
        else:
            # キャンセルされた場合は何もしない
            pass
    
    def _create_api_section(self) -> ft.Container:
        """APIチェックセクションの作成"""
        api_title = ft.Text(
            "LLM APIチェック",
            size=20,
            weight=ft.FontWeight.BOLD,
            text_align=ft.TextAlign.CENTER,
            color=ft.Colors.BLACK
        )
        
        # APIステータス表示用のテキスト
        openai_status = ft.Text(
            "OpenAI APIの状態：確認中...",
            size=14,
            color=ft.Colors.BLACK,
        )
        azure_status = ft.Text(
            "Azure Speech APIの状態：確認中...",
            size=14,
            color=ft.Colors.BLACK,
        )
        
        self.api_status_texts["OpenAI API"] = openai_status
        self.api_status_texts["Azure Speech API"] = azure_status
        
        return ft.Container(
            content=ft.Column(
                [
                    api_title,
                    ft.Container(height=10),
                    openai_status,
                    azure_status,
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            padding=20,
            border=ft.border.all(1, ft.Colors.GREY_400),
            border_radius=10,
            width=400,
        )
    
    def _create_audio_section(self) -> ft.Container:
        """音声チェックセクションの作成"""
        # マイク波形チャート
        self.mic_chart = ft.LineChart(
            data_series=[
                ft.LineChartData(
                    data_points=[],
                    stroke_width=2,
                    color=ft.Colors.BLUE,
                    below_line_bgcolor=ft.Colors.BLUE_100,
                )
            ],
            border=ft.border.Border(
                bottom=ft.BorderSide(4, ft.Colors.with_opacity(0.5, ft.Colors.ON_SURFACE)),
                left=ft.BorderSide(4, ft.Colors.with_opacity(0.5, ft.Colors.ON_SURFACE)),
                top=ft.BorderSide(4, ft.Colors.with_opacity(0.5, ft.Colors.ON_SURFACE)),
                right=ft.BorderSide(4, ft.Colors.with_opacity(0.5, ft.Colors.ON_SURFACE)),
            ),
            left_axis=ft.ChartAxis(
                labels_size=40,
            ),
            bottom_axis=ft.ChartAxis(
                labels_size=40,
            ),
            tooltip_bgcolor=ft.Colors.with_opacity(0.8, ft.Colors.BLUE_GREY),
            min_y=0.0,
            max_y=1.0,
            min_x=0,
            max_x=self.max_buffer_size,
            height=150,
            width=350,
        )
        
        # スピーカー波形チャート
        self.speaker_chart = ft.LineChart(
            data_series=[
                ft.LineChartData(
                    data_points=[],
                    stroke_width=2,
                    color=ft.Colors.GREEN,
                    below_line_bgcolor=ft.Colors.GREEN_100,
                )
            ],
            border=ft.border.Border(
                bottom=ft.BorderSide(4, ft.Colors.with_opacity(0.5, ft.Colors.ON_SURFACE)),
                left=ft.BorderSide(4, ft.Colors.with_opacity(0.5, ft.Colors.ON_SURFACE)),
                top=ft.BorderSide(4, ft.Colors.with_opacity(0.5, ft.Colors.ON_SURFACE)),
                right=ft.BorderSide(4, ft.Colors.with_opacity(0.5, ft.Colors.ON_SURFACE)),
            ),
            left_axis=ft.ChartAxis(
                labels_size=40,
            ),
            bottom_axis=ft.ChartAxis(
                labels_size=40,
            ),
            tooltip_bgcolor=ft.Colors.with_opacity(0.8, ft.Colors.BLUE_GREY),
            min_y=0.0,
            max_y=1.0,
            min_x=0,
            max_x=self.max_buffer_size,
            height=150,
            width=350,
        )
        
        # テストボタン
        self.test_button = ft.ElevatedButton(
            "「Hello」と発話してマイク・スピーカーをテスト",
            on_click=self._on_test_button_clicked,
            width=350,
            height=50,
        )
        
        # ステータステキスト
        self.status_text = ft.Text(
            "ボタンをクリックして「Hello」と発話してください",
            size=14,
            color=ft.Colors.BLACK,
            text_align=ft.TextAlign.CENTER
        )
        
        return ft.Container(
            content=ft.Column(
                [
                    ft.Text(
                        "マイク・スピーカーチェック",
                        size=20,
                        weight=ft.FontWeight.BOLD,
                        text_align=ft.TextAlign.CENTER,
                        color=ft.Colors.BLACK
                    ),
                    ft.Container(height=10),
                    ft.Row(
                        [
                            ft.Column(
                                [
                                    ft.Text("マイク", size=16, weight=ft.FontWeight.BOLD, color=ft.Colors.BLACK),
                                    self.mic_chart,
                                ],
                                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                            ),
                            ft.Container(width=20),
                            ft.Column(
                                [
                                    ft.Text("スピーカー", size=16, weight=ft.FontWeight.BOLD, color=ft.Colors.BLACK),
                                    self.speaker_chart,
                                ],
                                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                            ),
                        ],
                        alignment=ft.MainAxisAlignment.CENTER,
                    ),
                    ft.Container(height=20),
                    self.status_text,
                    ft.Container(height=10),
                    ft.Row([self.test_button], alignment=ft.MainAxisAlignment.CENTER),
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            padding=20,
            border=ft.border.all(1, ft.Colors.GREY_400),
            border_radius=10,
        )

    def _on_tab_changed(self, e: ft.ControlEvent) -> None:
        """タブが変更されたときの処理"""
        if not self.tabs:
            return
        
        # テスト実行中はタブの変更を無効化
        if self.test_running:
            # 現在のタブに戻す
            if self.current_test_id:
                current_index = next(
                    (i for i, item in enumerate(self.test_items) if item["id"] == self.current_test_id),
                    None
                )
                if current_index is not None:
                    self.tabs.selected_index = current_index
                    self.page.update()
            return
        
        selected_index = self.tabs.selected_index
        if selected_index is None or selected_index < 0 or selected_index >= len(self.test_items):
            return
        
        test_item = self.test_items[selected_index]
        test_id = test_item["id"]
        
        # メイン画面の場合はテストを開始しない
        if test_id == "main":
            # メイン画面の初期化（APIチェック、リアルタイム監視）
            self._initialize_main_tab()
            # 評価フィードバックを非表示（会話テストタブ以外では非表示）
            if self.evaluation_feedback_text:
                self.evaluation_feedback_text.visible = False
            self.page.update()
            return
        
        # 会話テスト以外のタブに移動した場合、評価フィードバックを非表示
        if test_id != "conversation":
            if self.evaluation_feedback_text:
                self.evaluation_feedback_text.visible = False
            self.page.update()
        
        # その他のテスト項目の場合は何もしない（ボタンクリック時のみ開始）

    def _on_reset_tests_clicked(self, e: ft.ControlEvent) -> None:
        """「テストを初めから実行するために，データを初期化する」ボタンがクリックされたときの処理"""
        # すべてのテスト履歴を削除
        self.storage_service.delete_test_progress()
        
        # テスト状態を初期化済みに変更
        self.test_initialized = True
        if self.test_status_text:
            self.test_status_text.value = "テストの状態：初期化済み"
        
        # すべてのタブタイマーを停止
        for test_id, timer_info in self.tab_timers.items():
            timer_info["running"] = False
            timer_info["start_time"] = None
            timer_info["final_time"] = None
            if timer_info["text"]:
                timer_info["text"].value = "テスト時間: 00:00:00"
        
        # 全体のタイマーを停止
        self.overall_timer_running = False
        self.overall_start_time = None
        if self.overall_timer_text:
            self.overall_timer_text.value = "実行時間: 00:00:00"
        
        # ステータステキストをリセット
        for test_id, status_text in self.tab_status_texts.items():
            test_item = next((item for item in self.test_items if item["id"] == test_id), None)
            if test_item:
                status_text.value = "「テストを開始する」ボタンをクリックしてテストを開始してください"
                status_text.color = ft.Colors.GREY_700
        
        self.page.update()
    
    def _on_test_start_button_clicked(self, test_id: str) -> None:
        """「テストを開始する」ボタンがクリックされたときの処理"""
        # テスト実行中フラグを設定
        self.test_running = True
        self.current_test_id = test_id
        
        # 他のタブを無効化（グレー表示）
        self._disable_other_tabs(test_id)
        
        # 「テストを一時停止する」と「テストを中断する」ボタンを表示
        if self.pause_test_button:
            self.pause_test_button.visible = True
            self.pause_test_button.text = "テストを一時停止する"
        if self.cancel_test_button:
            self.cancel_test_button.visible = True
        
        # 全体のタイマーを開始（まだ開始されていない場合）
        if not self.overall_timer_running:
            self.overall_start_time = datetime.now()
            self.overall_timer_running = True
            if self.overall_timer_thread is None or not self.overall_timer_thread.is_alive():
                self.overall_timer_thread = threading.Thread(target=self._update_overall_timer, daemon=True)
                self.overall_timer_thread.start()
        
        # タブのタイマーを開始
        if test_id in self.tab_timers:
            timer_info = self.tab_timers[test_id]
            timer_info["start_time"] = datetime.now()
            timer_info["running"] = True
            timer_info["final_time"] = None
            
            # タイマースレッドを開始
            if timer_info["thread"] is None or not timer_info["thread"].is_alive():
                timer_info["thread"] = threading.Thread(
                    target=self._update_tab_timer,
                    args=(test_id,),
                    daemon=True
                )
                timer_info["thread"].start()
        
        # 会話テストの場合は特別な処理
        if test_id == "conversation":
            self._start_conversation_test()
        
        # ステータステキストを更新
        if test_id in self.tab_status_texts:
            test_item = next((item for item in self.test_items if item["id"] == test_id), None)
            if test_item:
                status_text = self.tab_status_texts[test_id]
                status_text.value = f"テスト実行中: {test_item['name']}"
                status_text.color = ft.Colors.BLUE
                # グローバルステータステキストも更新（一時停止・中断ボタンの上に表示）
                if self.global_status_text:
                    self.global_status_text.value = status_text.value
                    self.global_status_text.color = status_text.color
        
        # ボタンを無効化
        if test_id in self.tab_start_buttons:
            self.tab_start_buttons[test_id].disabled = True
        
        self.page.update()
    
    def _start_conversation_test(self) -> None:
        """会話テストを開始"""
        if not self.roleplay_dropdown:
            return
        
        selected_roleplay = self.roleplay_dropdown.value
        
        # 「英会話講師との会話」の場合
        if selected_roleplay == "teacher":
            # Bob（男声）とAlice（女声）からランダムに選択
            teacher_name = random.choice(["Bob", "Alice"])
            # サポートされている音声: 'alloy', 'ash', 'ballad', 'coral', 'echo', 'sage', 'shimmer', 'verse', 'marin', 'cedar'
            # Bobは男声（echo, cedar, ashなど）、Aliceは女声（alloy, shimmer, coral, ballad, sage, verse, marinなど）
            if teacher_name == "Bob":
                voice = random.choice(["echo", "cedar", "ash"])  # 男声
            else:
                voice = random.choice(["alloy", "shimmer", "coral", "ballad", "sage", "verse", "marin"])  # 女声
            
            # プロンプトを設定（会話セッションの時間は変数で調整可能）
            system_prompt = f"""あなたは英会話講師であり，日本人の学生を相手に英会話のレッスンを行うのが仕事である．あなたはとても丁寧で，優しく，親切な人間だ．
学生が日本語を使ってしまったら，聞こえないフリや英語で喋るように指示をする．
学生の英語が聞き取れなければ，もう一度言ってもらうようにお願いする．
学生が君の英語を聞き取れないと言い出した時は，１度目は同じことをゆっくり言い直す．それでも分からない様子ならば，より優しい言い回しを使うようにする．
大体{self.conversation_session_duration_minutes}分程度の英会話セッションを行うことになっており，そのくらいの時間になったら，君から学生に対して，会話セッションの終了を伝えよう．

あなたの名前は{teacher_name}です。"""
            
            # ステータステキストを更新
            if "conversation" in self.tab_status_texts:
                status_text = self.tab_status_texts["conversation"]
                status_text.value = f"会話テスト実行中: {teacher_name}講師との会話"
                status_text.color = ft.Colors.BLUE
                # グローバルステータステキストも更新（一時停止・中断ボタンの上に表示）
                if self.global_status_text:
                    self.global_status_text.value = status_text.value
                    self.global_status_text.color = status_text.color
            
            # Realtime APIの接続を開始
            try:
                self.realtime_service = RealtimeService()
                # 会話履歴をリセット
                self.conversation_history = []
                # 評価モードと評価依頼回数をリセット（Realtime APIでの評価は使用しないが、変数は残す）
                self.evaluation_mode = False
                self.evaluation_request_count = 0
                # 評価スコア履歴をリセット
                self.evaluation_scores_history = []
                # 録音バッファをリセット
                with self.ai_audio_recording_lock:
                    self.ai_audio_recording_buffer.clear()
                with self.student_audio_recording_lock:
                    self.student_audio_recording_buffer.clear()
                # 評価フィードバックテキストをリセット
                self.evaluation_feedback_text.value = ""
                self.evaluation_feedback_text.visible = False
                
                success = self.realtime_service.connect(
                    system_prompt=system_prompt,
                    voice=voice,
                    on_audio_received=self._on_ai_audio_received,
                    on_text_received=self._on_ai_text_received,
                    on_student_transcript=self._on_student_transcript_received,
                    on_error=self._on_realtime_error,
                )
                
                if success:
                    self.conversation_running = True
                    # 学生の音声入力監視を開始（24kHzで録音）
                    # Realtime APIは24kHzを想定しているため、録音も24kHzで行う
                    self._start_student_audio_monitoring_24khz()
                    
                    # 最初の挨拶を送信（AIに会話を開始させる）
                    self.realtime_service.send_text("Hello, let's start the conversation.")
                else:
                    if "conversation" in self.tab_status_texts:
                        status_text = self.tab_status_texts["conversation"]
                        status_text.value = "Realtime APIへの接続に失敗しました。"
                        status_text.color = ft.Colors.RED
                        # グローバルステータステキストも更新
                        if self.global_status_text:
                            self.global_status_text.value = status_text.value
                            self.global_status_text.color = status_text.color
            except Exception as e:
                error_msg = f"Realtime API接続エラー: {str(e)}"
                if "conversation" in self.tab_status_texts:
                    status_text = self.tab_status_texts["conversation"]
                    status_text.value = error_msg
                    status_text.color = ft.Colors.RED
                    # グローバルステータステキストも更新
                    if self.global_status_text:
                        self.global_status_text.value = status_text.value
                        self.global_status_text.color = status_text.color
                print(error_msg)
            
        else:
            # 未実装のロールプレイ
            if "conversation" in self.tab_status_texts:
                status_text = self.tab_status_texts["conversation"]
                status_text.value = "このロールプレイはまだ実装されていません。"
                status_text.color = ft.Colors.RED
                # グローバルステータステキストも更新
                if self.global_status_text:
                    self.global_status_text.value = status_text.value
                    self.global_status_text.color = status_text.color
        
        self.page.update()
    
    def _on_ai_audio_received(self, audio_data: bytes) -> None:
        """AI音声データを受信したときの処理"""
        # 一時停止中は音声を受信しない
        if self.test_paused:
            return
        
        try:
            # 音声データが空でないことを確認
            if len(audio_data) == 0:
                return
            
            # 音声データをnumpy配列に変換（PCM16形式を想定）
            # Realtime APIはPCM16形式で音声を返す
            int16_array = np.frombuffer(audio_data, dtype=np.int16)
            float32_array: NDArray[np.floating] = int16_array.astype(np.float32)
            audio_array: NDArray[np.floating] = float32_array / 32768.0
            
            # データが有効か確認
            if len(audio_array) == 0:
                return
            
            # 音量を上げる（2.5倍に増幅、クリアさを保つため）
            # ノイズ除去のため、小さな値は0に近づける
            amplification_factor: float = 2.5
            amplified: NDArray[np.floating] = np.multiply(audio_array, amplification_factor)
            # ノイズゲート：非常に小さな値は0にする
            amplified = np.where(np.abs(amplified) < 0.001, 0.0, amplified)
            amplified = np.clip(amplified, -1.0, 1.0)
            
            # バッファキューに追加（途切れを防ぐため）
            with self.ai_audio_buffer_queue_lock:
                self.ai_audio_buffer_queue.append(amplified)
            
            # 録音バッファに追加（保存用、会話セッション中のみ）
            if self.conversation_running:
                with self.ai_audio_recording_lock:
                    self.ai_audio_recording_buffer.append(audio_array.copy())
            
            # ストリーミング再生を開始（まだ開始していない場合）
            if self.ai_audio_stream is None:
                self._start_ai_audio_stream()
                
        except Exception as e:
            print(f"AI音声処理エラー: {str(e)}")
    
    def _start_ai_audio_stream(self) -> None:
        """AI音声のストリーミング再生を開始"""
        try:
            # 24kHz、モノラル、float32形式でストリームを開く
            # バッファサイズを適切な値に設定（聞き取りやすさを優先）
            self.ai_audio_stream = sd.OutputStream(
                samplerate=24000,
                channels=1,
                dtype=np.float32,
                blocksize=16384,  # バッファサイズを適切な値に設定（聞き取りやすさを優先）
                latency='high'  # 高レイテンシーで安定性を確保
            )
            self.ai_audio_stream.start()
            
            # バッファから音声を再生するスレッドを開始
            def playback_thread():
                """バッファから音声を連続再生"""
                while self.conversation_running or len(self.ai_audio_buffer_queue) > 0:
                    # 一時停止中は再生しない
                    if self.test_paused:
                        time.sleep(0.1)
                        continue
                    
                    audio_chunk: NDArray[np.floating] | None = None
                    
                    # バッファキューからデータを取得
                    with self.ai_audio_buffer_queue_lock:
                        if len(self.ai_audio_buffer_queue) > 0:
                            # 複数のチャンクを結合して、より大きなチャンクで再生
                            chunks_to_combine: list[NDArray[np.floating]] = []
                            total_samples = 0
                            
                            # 最大32768サンプル（約1.36秒）まで結合（適切なバッファサイズで聞き取りやすさを優先）
                            while len(self.ai_audio_buffer_queue) > 0 and total_samples < 32768:
                                chunk: NDArray[np.floating] = self.ai_audio_buffer_queue.pop(0)
                                chunks_to_combine.append(chunk)
                                total_samples += len(chunk)
                            
                            if chunks_to_combine:
                                # チャンクを結合
                                audio_chunk = np.concatenate(chunks_to_combine)
                    
                    if audio_chunk is not None and len(audio_chunk) > 0:
                        # ストリームが存在し、アクティブな場合のみ書き込み
                        if self.ai_audio_stream is not None:
                            try:
                                # 2次元配列に変換（shape: (samples, 1)）
                                audio_2d = audio_chunk.reshape(-1, 1)
                                self.ai_audio_stream.write(audio_2d)
                            except Exception as e:
                                error_msg = str(e)
                                # PortAudioエラーの場合は、ストリームを再初期化
                                if "PortAudio" in error_msg or "PaErrorCode" in error_msg:
                                    try:
                                        if self.ai_audio_stream is not None:
                                            self.ai_audio_stream.stop()
                                            self.ai_audio_stream.close()
                                    except:
                                        pass
                                    self.ai_audio_stream = None
                                    # ストリームを再初期化
                                    time.sleep(0.1)
                                    try:
                                        self.ai_audio_stream = sd.OutputStream(
                                            samplerate=24000,
                                            channels=1,
                                            dtype=np.float32,
                                            blocksize=16384,
                                            latency='high'
                                        )
                                        self.ai_audio_stream.start()
                                        print("音声ストリームを再初期化しました")
                                    except Exception as e2:
                                        print(f"音声ストリーム再初期化エラー: {str(e2)}")
                                        self.ai_audio_stream = None
                                else:
                                    # その他のエラーはログに出力（頻繁に出力しない）
                                    pass
                        else:
                            # ストリームが存在しない場合は、バッファに戻す
                            with self.ai_audio_buffer_queue_lock:
                                # チャンクを分割してバッファに戻す（簡易実装）
                                chunk_size = 1024
                                for i in range(0, len(audio_chunk), chunk_size):
                                    self.ai_audio_buffer_queue.insert(0, audio_chunk[i:i+chunk_size])
                    else:
                        # バッファが空の場合は少し待機
                        time.sleep(0.01)
            
            playback_thread_obj = threading.Thread(target=playback_thread, daemon=True)
            playback_thread_obj.start()
            
        except Exception as e:
            print(f"音声ストリーム開始エラー: {str(e)}")
            self.ai_audio_stream = None
    
    def _stop_ai_audio_stream(self) -> None:
        """AI音声のストリーミング再生を停止"""
        if self.ai_audio_stream is not None:
            try:
                self.ai_audio_stream.stop()
                self.ai_audio_stream.close()
            except Exception as e:
                print(f"音声ストリーム停止エラー: {str(e)}")
            finally:
                self.ai_audio_stream = None
    
    def _on_ai_text_received(self, text: str) -> None:
        """AIテキストを受信したときの処理"""
        # テキストはログに出力（必要に応じてUIに表示）
        print(f"AI: {text}")
        # 会話履歴に追加
        self.conversation_history.append({"role": "ai", "text": text})
    
    def _start_student_audio_monitoring_24khz(self) -> None:
        """学生の音声入力監視を24kHzで開始（会話セッション開始時に呼ばれる）"""
        # 既に録音が開始されている場合は停止してから再開
        self._stop_student_audio_monitoring()
        
        def audio_callback_24khz(indata: NDArray[np.floating], frames: int, time_info: dict, status: sd.CallbackFlags) -> None:
            """24kHzでの音声コールバック"""
            if not self.conversation_running or not self.realtime_service or self.test_paused:
                return
            
            try:
                # 音声データを取得
                audio_data = indata[:, 0] if indata.shape[1] > 0 else indata.flatten()
                audio_list = audio_data.tolist()
                
                # 音声データをnumpy配列に変換
                np_data: NDArray[np.floating] = np.array(audio_list, dtype=np.float32)
                
                # 音声を増幅して、より大きな音声を送信（2.0倍に増幅）
                amplification_factor: float = 2.0
                multiplied_data: NDArray[np.floating] = np.multiply(np_data, amplification_factor)
                amplified_data: NDArray[np.floating] = np.clip(multiplied_data, -1.0, 1.0)
                
                # RMS値を計算して音声レベルを判定（増幅後のデータで判定）
                rms: float = float(np.sqrt(np.mean(amplified_data ** 2)))
                
                # 学生用の波形を更新（常に更新）
                if len(audio_list) > 0:
                    peak = np.max(np.abs(amplified_data))
                    value = (rms + peak) / 2.0
                    
                    # バッファに追加
                    self.student_waveform_buffer.append(value)
                    if len(self.student_waveform_buffer) > self.max_buffer_size:
                        self.student_waveform_buffer.pop(0)
                    
                    # 波形を更新
                    self._update_student_waveform()
                
                # 録音バッファに追加（保存用、増幅前の元データを使用、会話セッション中のみ）
                if self.conversation_running:
                    with self.student_audio_recording_lock:
                        self.student_audio_recording_buffer.append(np_data.copy())
                
                # 音声検出：RMS値が閾値以上の時のみ送信
                # サーバー側のVADも使用するが、クライアント側でも軽いVADを実装してノイズを除外
                # 参考プロジェクトでは常に送信しているが、環境ノイズが多い場合は誤検出が発生する可能性がある
                if rms >= self.audio_threshold:
                    # 16bit PCM形式に変換（増幅後のデータを使用）
                    pcm_scale_factor: float = 32767.0
                    scaled_data: NDArray[np.floating] = np.multiply(amplified_data, pcm_scale_factor)
                    pcm_data: NDArray[np.integer] = scaled_data.astype(np.int16)
                    audio_bytes = pcm_data.tobytes()
                    
                    # Realtime APIに送信
                    success = self.realtime_service.send_audio(audio_bytes)
                    
                    # デバッグ用：送信状況をログに出力（最初の数回のみ）
                    if success:
                        self.audio_send_count += 1
                        current_time = time.time()
                        if self.audio_send_count <= 20 or (current_time - self.last_audio_send_time) > 2.0:
                            print(f"音声送信: RMS={rms:.4f}, サイズ={len(audio_bytes)} bytes, 回数={self.audio_send_count}")
                            self.last_audio_send_time = current_time
                    
            except Exception as e:
                print(f"学生音声処理エラー: {str(e)}")
        
        # 24kHzで録音を開始
        def start_recording():
            try:
                self.student_recording_stream = sd.InputStream(
                    samplerate=24000,  # Realtime APIは24kHzを想定
                    channels=1,
                    dtype=np.float32,
                    blocksize=1024,
                    callback=audio_callback_24khz
                )
                self.student_recording_stream.start()
                while self.conversation_running:
                    time.sleep(0.1)
            except Exception as e:
                print(f"24kHz録音エラー: {str(e)}")
            finally:
                # ストリームを停止
                stream = self.student_recording_stream
                if stream is not None:
                    try:
                        stream.stop()
                        stream.close()
                    except Exception as e:
                        print(f"録音ストリーム停止エラー: {str(e)}")
                    finally:
                        self.student_recording_stream = None
        
        self.student_recording_thread = threading.Thread(target=start_recording, daemon=True)
        self.student_recording_thread.start()
    
    def _stop_student_audio_monitoring(self) -> None:
        """学生の音声入力監視を停止（会話セッション終了時に呼ばれる）"""
        # 録音ストリームを停止
        if self.student_recording_stream is not None:
            try:
                self.student_recording_stream.stop()
                self.student_recording_stream.close()
            except Exception as e:
                print(f"録音ストリーム停止エラー: {str(e)}")
            finally:
                self.student_recording_stream = None
        
        # 録音スレッドの終了を待つ
        if self.student_recording_thread is not None:
            self.student_recording_thread.join(timeout=1.0)
            self.student_recording_thread = None
    
    def _on_student_audio_received(self, audio_data: list[float]) -> None:
        """学生の音声データを受信したときの処理（旧メソッド、互換性のため残す）"""
        # このメソッドは24kHz監視が使用されるため、使用されない
        pass
    
    def _on_student_transcript_received(self, transcript: str) -> None:
        """学生の音声転写を受信したときの処理"""
        print(f"学生: {transcript}")
        # 会話履歴に追加
        self.conversation_history.append({"role": "student", "text": transcript})
        # 会話中の評価は削除（ヒントになってしまうため、最終評価のみ実行）
    
    def _on_realtime_error(self, error_msg: str) -> None:
        """Realtime APIエラー時の処理"""
        print(f"Realtime APIエラー: {error_msg}")
        if "conversation" in self.tab_status_texts:
            status_text = self.tab_status_texts["conversation"]
            status_text.value = f"エラー: {error_msg}"
            status_text.color = ft.Colors.RED
            # グローバルステータステキストも更新
            if self.global_status_text:
                self.global_status_text.value = status_text.value
                self.global_status_text.color = status_text.color
        self.page.update()
    
    def _update_student_waveform(self) -> None:
        """学生用の波形を更新"""
        if not self.student_waveform_chart:
            return
        
        try:
            data_points: list[ft.LineChartDataPoint] = []
            buffer_size = len(self.student_waveform_buffer)
            
            if buffer_size > 0:
                for i, value in enumerate(self.student_waveform_buffer):
                    normalized_value = max(0.0, min(1.0, value * 10.0))
                    data_points.append(ft.LineChartDataPoint(i, normalized_value))
            else:
                data_points = [ft.LineChartDataPoint(i, 0.0) for i in range(self.max_buffer_size)]
            
            self.student_waveform_chart.max_x = max(self.max_buffer_size, buffer_size)
            
            if self.student_waveform_chart.data_series and len(self.student_waveform_chart.data_series) > 0:
                self.student_waveform_chart.data_series[0].data_points = data_points
                self.page.update()
        except Exception as e:
            print(f"学生波形更新エラー: {str(e)}")
    
    def _disable_other_tabs(self, active_test_id: str) -> None:
        """他のタブを無効化（グレー表示）"""
        if not self.tabs:
            return
        
        # 選択されていないタブの色をグレーに変更
        self.tabs.unselected_label_color = ft.Colors.GREY_400
        self.page.update()
    
    def _enable_all_tabs(self) -> None:
        """すべてのタブを有効化（白表示）"""
        if not self.tabs:
            return
        
        # 選択されていないタブの色を黒に戻す
        self.tabs.unselected_label_color = ft.Colors.BLACK
        self.page.update()
    
    def _on_pause_test_clicked(self, e: ft.ControlEvent) -> None:
        """「テストを一時停止する」/「テストを再開する」ボタンがクリックされたときの処理"""
        if not self.current_test_id or not self.pause_test_button:
            return
        
        if self.test_paused:
            # 再開処理
            self.test_paused = False
            self.pause_test_button.text = "テストを一時停止する"
            
            # 会話テストの場合は音声送受信を再開
            if self.current_test_id == "conversation":
                # 音声ストリームは既に開始されているので、conversation_runningフラグで制御
                # 特に追加の処理は不要（audio_callback_24khzが自動的に再開される）
                pass
            
            # ステータステキストを更新
            if self.current_test_id in self.tab_status_texts:
                test_item = next((item for item in self.test_items if item["id"] == self.current_test_id), None)
                if test_item:
                    status_text = self.tab_status_texts[self.current_test_id]
                    status_text.value = f"テスト実行中: {test_item['name']}"
                    status_text.color = ft.Colors.BLUE
                    # グローバルステータステキストも更新
                    if self.global_status_text:
                        self.global_status_text.value = status_text.value
                        self.global_status_text.color = status_text.color
            
            print("テストを再開しました")
        else:
            # 一時停止処理
            self.test_paused = True
            self.pause_test_button.text = "テストを再開する"
            
            # 会話テストの場合は音声送受信を一時停止
            if self.current_test_id == "conversation":
                # 音声ストリームは停止しない（接続を維持）
                # audio_callback_24khzがtest_pausedフラグをチェックして送信を停止する
                # AI音声の再生も停止（バッファキューをクリア）
                with self.ai_audio_buffer_queue_lock:
                    self.ai_audio_buffer_queue.clear()
            
            # ステータステキストを更新
            if self.current_test_id in self.tab_status_texts:
                test_item = next((item for item in self.test_items if item["id"] == self.current_test_id), None)
                if test_item:
                    status_text = self.tab_status_texts[self.current_test_id]
                    status_text.value = f"テスト一時停止中: {test_item['name']}"
                    status_text.color = ft.Colors.ORANGE
                    # グローバルステータステキストも更新
                    if self.global_status_text:
                        self.global_status_text.value = status_text.value
                        self.global_status_text.color = status_text.color
            
            print("テストを一時停止しました")
        
        self.page.update()
    
    def _on_cancel_test_clicked(self, e: ft.ControlEvent) -> None:
        """「テストを中断する」ボタンがクリックされたときの処理"""
        if not self.current_test_id:
            return
        
        # 会話テストの場合はRealtime APIを切断
        if self.current_test_id == "conversation" and self.realtime_service:
            self.conversation_running = False
            # 録音を停止（会話セッション終了時）
            self._stop_student_audio_monitoring()
            # 音声ストリームを停止
            self._stop_ai_audio_stream()
            # バッファキューをクリア
            with self.ai_audio_buffer_queue_lock:
                self.ai_audio_buffer_queue.clear()
            # 少し待機して再生が完了するのを待つ
            time.sleep(0.5)
            self.realtime_service.disconnect()
            self.realtime_service = None
            self.audio_service.stop_mic_monitoring()
            
            # 会話終了後に最終評価を実行（最終評価のみ表示）
            if len(self.conversation_history) > 0:
                self._evaluate_conversation_async(is_final=True)
        
        # テスト実行中フラグを解除
        self.test_running = False
        
        # タブのタイマーを停止（データを保存しない）
        if self.current_test_id in self.tab_timers:
            timer_info = self.tab_timers[self.current_test_id]
            timer_info["running"] = False
            timer_info["start_time"] = None
            timer_info["final_time"] = None
            if timer_info["text"]:
                timer_info["text"].value = "テスト時間: 00:00:00"
        
        # ステータステキストをリセット
        if self.current_test_id in self.tab_status_texts:
            test_item = next((item for item in self.test_items if item["id"] == self.current_test_id), None)
            if test_item:
                status_text = self.tab_status_texts[self.current_test_id]
                status_text.value = "「テストを開始する」ボタンをクリックしてテストを開始してください"
                status_text.color = ft.Colors.GREY_700
                # グローバルステータステキストも更新
                if self.global_status_text:
                    self.global_status_text.value = status_text.value
                    self.global_status_text.color = status_text.color
        
        # ボタンを再有効化
        if self.current_test_id in self.tab_start_buttons:
            self.tab_start_buttons[self.current_test_id].disabled = False
        
        # すべてのタブを有効化
        self._enable_all_tabs()
        
        # 「テストを一時停止する」と「テストを中断する」ボタンを非表示
        if self.pause_test_button:
            self.pause_test_button.visible = False
        if self.cancel_test_button:
            self.cancel_test_button.visible = False
        
        # 一時停止状態をリセット
        self.test_paused = False
        
        self.current_test_id = None
        self.page.update()
    
    def _stop_test_timer(self, test_id: str) -> None:
        """テストのタイマーを停止（正常終了時）"""
        if test_id in self.tab_timers:
            timer_info = self.tab_timers[test_id]
            timer_info["running"] = False
            
            # 最終時間を保存
            if timer_info["start_time"] and timer_info["text"]:
                elapsed = datetime.now() - timer_info["start_time"]
                hours, remainder = divmod(int(elapsed.total_seconds()), 3600)
                minutes, seconds = divmod(remainder, 60)
                final_time_str = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
                timer_info["final_time"] = final_time_str
                timer_info["text"].value = f"テスト時間: {final_time_str}"
                
                # 進捗を保存
                progress_data = {
                    "test_id": test_id,
                    "final_time": final_time_str,
                    "completed_at": datetime.now().isoformat(),
                }
                self.storage_service.save_test_progress(test_id, progress_data)
            
            # 会話テストの場合はRealtime APIを切断して最終評価を実行
            if test_id == "conversation":
                # ステータステキストを「会話セッション終了」に更新（会話テストタブのみ）
                if "conversation" in self.tab_status_texts:
                    status_text = self.tab_status_texts["conversation"]
                    status_text.value = "会話セッション終了"
                    status_text.color = ft.Colors.GREY_700
                
                if self.realtime_service:
                    self.conversation_running = False
                    # 録音を停止（会話セッション終了時）
                    self._stop_student_audio_monitoring()
                    # 音声ストリームを停止
                    self._stop_ai_audio_stream()
                    # バッファキューをクリア
                    with self.ai_audio_buffer_queue_lock:
                        self.ai_audio_buffer_queue.clear()
                    # 少し待機して再生が完了するのを待つ
                    time.sleep(0.5)
                    self.realtime_service.disconnect()
                    self.realtime_service = None
                    self.audio_service.stop_mic_monitoring()
                
                if len(self.conversation_history) > 0:
                    self._evaluate_conversation_async(is_final=True)
            
            # テスト実行中フラグを解除
            self.test_running = False
            
            # すべてのタブを有効化
            self._enable_all_tabs()
            
            # 「テストを一時停止する」と「テストを中断する」ボタンを非表示
            if self.pause_test_button:
                self.pause_test_button.visible = False
            if self.cancel_test_button:
                self.cancel_test_button.visible = False
            
            # 一時停止状態をリセット
            self.test_paused = False
            
            self.current_test_id = None
            self.page.update()
    
    def _update_overall_timer(self) -> None:
        """全体の実行時間タイマーを更新"""
        while self.overall_timer_running:
            if self.overall_start_time and self.overall_timer_text and not self.test_paused:
                elapsed = datetime.now() - self.overall_start_time
                hours, remainder = divmod(int(elapsed.total_seconds()), 3600)
                minutes, seconds = divmod(remainder, 60)
                time_str = f"実行時間: {hours:02d}:{minutes:02d}:{seconds:02d}"
                self.overall_timer_text.value = time_str
                self.page.update()
            time.sleep(1)
    
    def _update_tab_timer(self, test_id: str) -> None:
        """タブ内のタイマーを更新"""
        if test_id not in self.tab_timers:
            return
        
        timer_info = self.tab_timers[test_id]
        paused_start_time: datetime | None = None  # 一時停止開始時刻
        
        while timer_info["running"]:
            if timer_info["start_time"] and timer_info["text"]:
                if self.test_paused:
                    # 一時停止中はタイマーを更新しない
                    if paused_start_time is None:
                        paused_start_time = datetime.now()
                    time.sleep(1)
                    continue
                else:
                    # 再開時、一時停止時間を補正
                    if paused_start_time is not None:
                        pause_duration = datetime.now() - paused_start_time
                        timer_info["start_time"] = timer_info["start_time"] + pause_duration
                        paused_start_time = None
                    
                    elapsed = datetime.now() - timer_info["start_time"]
                    hours, remainder = divmod(int(elapsed.total_seconds()), 3600)
                    minutes, seconds = divmod(remainder, 60)
                    time_str = f"テスト時間: {hours:02d}:{minutes:02d}:{seconds:02d}"
                    timer_info["text"].value = time_str
                    self.page.update()
                    
                    # 会話テストの場合、指定時間が経過したら自動的に終了
                    if test_id == "conversation":
                        elapsed_minutes = elapsed.total_seconds() / 60.0
                        if elapsed_minutes >= self.conversation_session_duration_minutes:
                            print(f"会話セッションの時間（{self.conversation_session_duration_minutes}分）が経過したため、会話を終了します。")
                            # 会話を終了
                            self._stop_test_timer(test_id)
                            return
            time.sleep(1)

    
    def _update_tab_content(self, test_id: str) -> None:
        """タブのコンテンツを更新"""
        if test_id not in self.tab_status_texts:
            return
        
        test_item = next((item for item in self.test_items if item["id"] == test_id), None)
        if not test_item:
            return
        
        # ステータステキストを更新
        status_text = self.tab_status_texts[test_id]
        status_text.value = f"テスト実行中: {test_item['name']}"
        status_text.color = ft.Colors.BLUE
        
        self.page.update()
    
    def _format_conversation_history(self) -> str:
        """会話履歴をテキスト形式に変換"""
        if not self.conversation_history:
            return ""
        
        lines: list[str] = []
        for entry in self.conversation_history:
            role = entry.get("role", "")
            text = entry.get("text", "")
            if role == "ai":
                lines.append(f"AI「{text}」")
            elif role == "student":
                lines.append(f"学生「{text}」")
        
        return "\n".join(lines)
    
    def _evaluate_conversation_async(self, is_final: bool = False) -> None:
        """会話を非同期で評価（バックグラウンドで実行、音声処理をブロックしない）
        
        Args:
            is_final: 最終評価の場合True（ステータステキストに表示する）
        """
        async def evaluate_async():
            """評価を非同期で実行"""
            try:
                # 会話履歴をテキスト形式に変換（メインスレッドから取得）
                conversation_text = self._format_conversation_history()
                if not conversation_text:
                    return
                
                # 評価サービスを呼び出し（完全に非同期で実行、音声処理をブロックしない）
                evaluation_result = await self.evaluation_service.openai_service.evaluate_conversation(conversation_text)
                
                # 評価結果を処理（スコアをグラフに追加、最終評価のみ表示）
                if "error" not in evaluation_result:
                    grammar_score = evaluation_result.get("grammar_score", 0)
                    vocabulary_score = evaluation_result.get("vocabulary_score", 0)
                    naturalness_score = evaluation_result.get("naturalness_score", 0)
                    fluency_score = evaluation_result.get("fluency_score", 0)
                    overall_score = evaluation_result.get("overall_score", 0)
                    feedback = evaluation_result.get("evaluation", "")
                    
                    # スコア履歴に追加
                    self.evaluation_scores_history.append({
                        "grammar": grammar_score,
                        "vocabulary": vocabulary_score,
                        "naturalness": naturalness_score,
                        "fluency": fluency_score,
                        "overall": overall_score,
                    })
                    
                    # 折れ線グラフを更新（点数はグラフのみで表示、テキスト表示は削除）
                    self._update_score_chart()
                    
                    # 最終評価の場合、評価スコアと講評を画面下に表示
                    if is_final:
                        self._display_evaluation_feedback(grammar_score, vocabulary_score, naturalness_score, fluency_score, overall_score, feedback)
                        # データを非同期で保存（UIをブロックしない）
                        await self._save_conversation_data_async(grammar_score, vocabulary_score, naturalness_score, fluency_score, overall_score, feedback)
                else:
                    error_msg = evaluation_result.get("error", "評価エラー")
                    if "conversation" in self.tab_status_texts:
                        status_text = self.tab_status_texts["conversation"]
                        status_text.value = f"評価エラー: {error_msg}"
                        status_text.color = ft.Colors.RED
                        self.page.update()
            except Exception as e:
                print(f"会話評価エラー: {str(e)}")
                if "conversation" in self.tab_status_texts:
                    status_text = self.tab_status_texts["conversation"]
                    status_text.value = f"評価エラー: {str(e)}"
                    status_text.color = ft.Colors.RED
                    self.page.update()
        
        # 評価を非同期で実行（音声処理をブロックしない）
        # 既存のイベントループがある場合はタスクとしてスケジュール、ない場合は別スレッドで新しいループを実行
        try:
            # 実行中のイベントループを取得（存在する場合）
            # ループが存在することを確認するためだけに呼び出す
            _ = asyncio.get_running_loop()
            # 既存のループでタスクをスケジュール（既存のイベントループと統合）
            asyncio.create_task(evaluate_async())
        except RuntimeError:
            # 実行中のループがない場合は、別スレッドで新しいループを作成して実行
            # これにより、メインスレッドや音声処理スレッドをブロックしない
            def evaluate_thread():
                """評価を実行するスレッド（新しいイベントループで実行）"""
                try:
                    asyncio.run(evaluate_async())
                except Exception as e:
                    print(f"評価スレッドエラー: {str(e)}")
            
            evaluation_thread_obj = threading.Thread(target=evaluate_thread, daemon=True)
            evaluation_thread_obj.start()
    
    def _request_evaluation_from_realtime(self) -> None:
        """Realtime APIのセッション内で評価を依頼"""
        if not self.realtime_service or not self.conversation_running:
            return
        
        # 重複評価を防ぐ（同じ会話履歴に対して複数回評価しない）
        current_history_length = len(self.conversation_history)
        if self.evaluation_request_count >= current_history_length:
            return  # 既に評価済み
        
        self.evaluation_request_count = current_history_length
        
        # 評価を依頼するテキストメッセージを送信
        evaluation_request = """Please evaluate our conversation so far. Evaluate the following aspects:
1. Whether the conversation is natural and flowing
2. Grammar accuracy
3. Vocabulary appropriateness
4. Naturalness of conversation
5. Conversation fluency

Please respond in JSON format:
{
    "is_valid": true/false,
    "grammar_score": 0-100,
    "vocabulary_score": 0-100,
    "naturalness_score": 0-100,
    "fluency_score": 0-100,
    "overall_score": 0-100,
    "feedback": "evaluation comment"
}"""
        
        # 評価モードを有効化
        self.evaluation_mode = True
        
        # 評価依頼を送信
        success = self.realtime_service.send_text(evaluation_request)
        if not success:
            self.evaluation_mode = False
            print("Realtime APIでの評価依頼に失敗しました")
    
    def _parse_evaluation_from_realtime_response(self, text: str) -> None:
        """Realtime APIからの評価結果を解析"""
        try:
            # JSON形式の部分を抽出（```json ... ``` または { ... } の形式）
            json_match = re.search(r'\{[^{}]*"is_valid"[^{}]*\}', text, re.DOTALL)
            if not json_match:
                # より広範囲に検索
                json_match = re.search(r'\{.*"is_valid".*\}', text, re.DOTALL)
            
            if json_match:
                json_str = json_match.group(0)
                evaluation_data = json.loads(json_str)
                
                is_valid = evaluation_data.get("is_valid", False)
                overall_score = evaluation_data.get("overall_score", 0)
                feedback = evaluation_data.get("feedback", "")
                
                # ステータステキストを更新（Realtime API評価）
                if "conversation" in self.tab_status_texts:
                    status_text = self.tab_status_texts["conversation"]
                    # 既存の評価結果と統合して表示
                    if is_valid:
                        status_text.value = f"会話評価（Realtime API）: 成立（総合スコア: {overall_score:.1f}/100）\n{feedback}"
                        status_text.color = ft.Colors.GREEN
                    else:
                        status_text.value = f"会話評価（Realtime API）: 不成立（総合スコア: {overall_score:.1f}/100）\n{feedback}"
                        status_text.color = ft.Colors.ORANGE
                    self.page.update()
            else:
                # JSON形式でない場合は、テキスト全体をフィードバックとして使用
                if "conversation" in self.tab_status_texts:
                    status_text = self.tab_status_texts["conversation"]
                    status_text.value = f"会話評価（Realtime API）: {text}"
                    status_text.color = ft.Colors.BLUE
                    self.page.update()
        except json.JSONDecodeError as e:
            print(f"Realtime API評価結果のJSON解析エラー: {str(e)}")
            # JSON解析に失敗した場合は、テキスト全体をフィードバックとして使用
            if "conversation" in self.tab_status_texts:
                status_text = self.tab_status_texts["conversation"]
                status_text.value = f"会話評価（Realtime API）: {text}"
                status_text.color = ft.Colors.BLUE
                self.page.update()
        except Exception as e:
            print(f"Realtime API評価結果の解析エラー: {str(e)}")
    
    def _update_score_chart(self) -> None:
        """評価スコアの折れ線グラフを更新"""
        if not self.score_chart:
            return
        
        try:
            history_size = len(self.evaluation_scores_history)
            # 空のデータでもグラフを表示（初期状態でも表示されるように）
            if history_size == 0:
                # 空のデータポイントを設定（グラフが表示されるように）
                empty_points: list[ft.LineChartDataPoint] = []
                if self.score_chart.data_series and len(self.score_chart.data_series) >= 5:
                    self.score_chart.data_series[0].data_points = empty_points
                    self.score_chart.data_series[1].data_points = empty_points
                    self.score_chart.data_series[2].data_points = empty_points
                    self.score_chart.data_series[3].data_points = empty_points
                    self.score_chart.data_series[4].data_points = empty_points
                    self.page.update()
                return
            
            # 各スコアのデータポイントを生成
            # 0: grammar, 1: vocabulary, 2: naturalness, 3: fluency, 4: overall
            grammar_points: list[ft.LineChartDataPoint] = []
            vocabulary_points: list[ft.LineChartDataPoint] = []
            naturalness_points: list[ft.LineChartDataPoint] = []
            fluency_points: list[ft.LineChartDataPoint] = []
            overall_points: list[ft.LineChartDataPoint] = []
            
            for i, score_data in enumerate(self.evaluation_scores_history):
                grammar_points.append(ft.LineChartDataPoint(i, score_data.get("grammar", 0)))
                vocabulary_points.append(ft.LineChartDataPoint(i, score_data.get("vocabulary", 0)))
                naturalness_points.append(ft.LineChartDataPoint(i, score_data.get("naturalness", 0)))
                fluency_points.append(ft.LineChartDataPoint(i, score_data.get("fluency", 0)))
                overall_points.append(ft.LineChartDataPoint(i, score_data.get("overall", 0)))
            
            # グラフのX軸範囲を調整
            max_x = max(history_size, 10)
            self.score_chart.max_x = max_x
            
            # データポイントを更新
            if self.score_chart.data_series and len(self.score_chart.data_series) >= 5:
                self.score_chart.data_series[0].data_points = grammar_points
                self.score_chart.data_series[1].data_points = vocabulary_points
                self.score_chart.data_series[2].data_points = naturalness_points
                self.score_chart.data_series[3].data_points = fluency_points
                self.score_chart.data_series[4].data_points = overall_points
                self.page.update()
        except Exception as e:
            print(f"スコアグラフ更新エラー: {str(e)}")
    
    def _display_evaluation_feedback(self, grammar_score: float, vocabulary_score: float, naturalness_score: float, fluency_score: float, overall_score: float, feedback: str) -> None:
        """評価スコアと講評を会話テストタブ内に表示"""
        # 現在のタブが会話テストでない場合は表示しない
        if not self.tabs or self.tabs.selected_index is None:
            return
        
        selected_index = self.tabs.selected_index
        if selected_index < 0 or selected_index >= len(self.test_items):
            return
        
        current_test_id = self.test_items[selected_index]["id"]
        if current_test_id != "conversation":
            # 会話テストタブ以外では表示しない
            return
        
        feedback_text = f"""評価スコア
文法: {grammar_score:.1f}/100 | 語彙: {vocabulary_score:.1f}/100 | 会話の自然さ: {naturalness_score:.1f}/100 | 流暢さ: {fluency_score:.1f}/100
総合スコア: {overall_score:.1f}/100

講評:
{feedback}"""
        
        self.evaluation_feedback_text.value = feedback_text
        self.evaluation_feedback_text.visible = True
        self.page.update()
    
    async def _save_conversation_data_async(self, grammar_score: float, vocabulary_score: float, naturalness_score: float, fluency_score: float, overall_score: float, feedback: str) -> None:
        """会話データを非同期で保存（書き起こし、mp3、評価スコアと講評）
        
        このメソッドは非同期で実行され、UIをブロックしません。
        """
        try:
            # 保存ディレクトリを使用（選択された保存場所またはデフォルトのDesktop）
            base_save_dir = self.save_directory
            base_save_dir.mkdir(parents=True, exist_ok=True)
            
            # テストIDを取得（会話テストの場合は"conversation"）
            test_id = self.current_test_id if self.current_test_id else "conversation"
            
            # TestRecord_テストID_YYYYMMDD_適当な番号というフォルダ名を生成
            date_str = datetime.now().strftime("%Y%m%d")
            # 同じ日付・同じテストIDのTestRecordフォルダ数をカウントして番号を決定
            existing_folders = list(base_save_dir.glob(f"TestRecord_{test_id}_{date_str}_*"))
            folder_number = len(existing_folders) + 1
            record_folder_name = f"TestRecord_{test_id}_{date_str}_{folder_number:03d}"
            
            # レコードフォルダを作成
            save_dir = base_save_dir / record_folder_name
            save_dir.mkdir(parents=True, exist_ok=True)
            
            # ファイル名を生成（テストIDを含める）
            base_filename = f"{test_id}_{date_str}_{folder_number:03d}"
            
            # 会話の書き起こしを取得
            conversation_text = self._format_conversation_history()
            
            # JSONデータを作成
            json_data = {
                "conversation_transcript": conversation_text,
                "evaluation": {
                    "grammar_score": grammar_score,
                    "vocabulary_score": vocabulary_score,
                    "naturalness_score": naturalness_score,
                    "fluency_score": fluency_score,
                    "overall_score": overall_score,
                    "feedback": feedback,
                },
                "timestamp": datetime.now().isoformat(),
            }
            
            # JSONファイルを非同期で保存
            json_path = save_dir / f"{base_filename}.json"
            json_str = json.dumps(json_data, ensure_ascii=False, indent=2)
            async with aiofiles.open(json_path, 'w', encoding='utf-8') as f:
                await f.write(json_str)
            
            # AI音声をmp3に保存（CPU集約的な処理なので別スレッドで実行）
            with self.ai_audio_recording_lock:
                if len(self.ai_audio_recording_buffer) > 0:
                    ai_audio_combined = np.concatenate(self.ai_audio_recording_buffer)
                    ai_audio_path = save_dir / f"{base_filename}_ai.mp3"
                    # float32形式の音声データをint16に変換
                    ai_audio_int16 = (np.clip(ai_audio_combined, -1.0, 1.0) * 32767.0).astype(np.int16)
                    # numpy配列をAudioSegmentに変換してmp3として保存
                    audio_segment = AudioSegment(
                        ai_audio_int16.tobytes(),
                        frame_rate=24000,
                        channels=1,
                        sample_width=2  # int16 = 2 bytes
                    )
                    # CPU集約的な処理は別スレッドで実行（UIをブロックしない）
                    await asyncio.to_thread(audio_segment.export, ai_audio_path, format="mp3", bitrate="64k")
            
            # 学生音声をmp3に保存（CPU集約的な処理なので別スレッドで実行）
            with self.student_audio_recording_lock:
                if len(self.student_audio_recording_buffer) > 0:
                    student_audio_combined = np.concatenate(self.student_audio_recording_buffer)
                    student_audio_path = save_dir / f"{base_filename}_student.mp3"
                    # float32形式の音声データをint16に変換
                    student_audio_int16 = (np.clip(student_audio_combined, -1.0, 1.0) * 32767.0).astype(np.int16)
                    # numpy配列をAudioSegmentに変換してmp3として保存
                    audio_segment = AudioSegment(
                        student_audio_int16.tobytes(),
                        frame_rate=24000,
                        channels=1,
                        sample_width=2  # int16 = 2 bytes
                    )
                    # CPU集約的な処理は別スレッドで実行（UIをブロックしない）
                    await asyncio.to_thread(audio_segment.export, student_audio_path, format="mp3", bitrate="64k")
            
            print(f"会話データを保存しました: {json_path}")
            
            # ステータステキストに保存パスを表示（会話テストタブのみ）
            save_message = f"会話データを保存しました: {json_path}"
            if "conversation" in self.tab_status_texts:
                status_text = self.tab_status_texts["conversation"]
                # 「会話セッション終了」の次の行に保存パスを表示
                if status_text.value == "会話セッション終了":
                    status_text.value = f"会話セッション終了\n{save_message}"
                else:
                    status_text.value = f"{status_text.value}\n{save_message}"
                status_text.color = ft.Colors.GREY_700
                # UIを更新
                self.page.update()
            
        except Exception as e:
            print(f"会話データの保存エラー: {str(e)}")
            traceback.print_exc()
    
    def _save_conversation_data(self, grammar_score: float, vocabulary_score: float, naturalness_score: float, fluency_score: float, overall_score: float, feedback: str) -> None:
        """会話データを保存（非推奨: 後方互換性のため残す）
        
        このメソッドは非推奨です。代わりに`_save_conversation_data_async`を使用してください。
        """
        # 非同期メソッドを呼び出す（既存のイベントループを使用）
        try:
            # 実行中のイベントループを取得（存在する場合）
            # 既存のループでタスクをスケジュール（既存のイベントループと統合）
            asyncio.create_task(self._save_conversation_data_async(grammar_score, vocabulary_score, naturalness_score, fluency_score, overall_score, feedback))
        except RuntimeError:
            # 実行中のループがない場合は、別スレッドで新しいループを作成して実行
            # これにより、メインスレッドや音声処理スレッドをブロックしない
            def save_thread():
                """保存を実行するスレッド（新しいイベントループで実行）"""
                try:
                    asyncio.run(self._save_conversation_data_async(grammar_score, vocabulary_score, naturalness_score, fluency_score, overall_score, feedback))
                except Exception as e:
                    print(f"保存スレッドエラー: {str(e)}")
            
            save_thread_obj = threading.Thread(target=save_thread, daemon=True)
            save_thread_obj.start()
    
    def _create_listening_test_content(self) -> ft.Container:
        """リスニングテストタブのコンテンツを作成"""
        content = ft.Column(
            [
                ft.Text("リスニングテストのコンテンツはここに表示されます。", size=16),
                # 追加のUIコンポーネントをここに配置
            ],
            scroll=ft.ScrollMode.AUTO,
            expand=True,
            
            start_button = ft.ElevatedButton(
            "テストを開始する",
            on_click=lambda e, tid=test_id: self._on_test_start_button_clicked(tid),
            width=250,
            height=45,
        )
        )
        return ft.Container(content=content, padding=10)

