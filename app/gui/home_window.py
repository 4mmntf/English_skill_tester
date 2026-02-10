"""
ホーム画面のGUIコンポーネント
"""
import flet as ft
import threading
import time
from typing import Callable
import numpy as np
from app.services.audio_service import AudioService
from app.services.api_check_service import APICheckService


class HomeWindow:
    """ホーム画面のウィンドウクラス"""
    
    def __init__(self, page: ft.Page, on_start_callback: Callable[[], None] | None = None) -> None:
        """
        初期化処理
        
        Args:
            page: Fletのページオブジェクト
            on_start_callback: 開始ボタンがクリックされたときに呼ばれるコールバック関数
        """
        self.page = page
        self.on_start_callback = on_start_callback
        self.audio_service = AudioService()
        self.api_check_service = APICheckService()
        
        # 録音状態
        self.is_recording: bool = False
        self.recorded_audio: list[float] | None = None
        
        # リアルタイム波形表示用
        self.mic_waveform_buffer: list[float] = []
        self.speaker_waveform_buffer: list[float] = []
        self.max_buffer_size: int = 200  # 表示するデータポイント数
        self.last_update_time: float = 0.0
        self.update_interval: float = 0.05  # 50ms間隔で更新（20fps）
        
        # UIコンポーネント
        self.mic_chart: ft.LineChart | None = None
        self.speaker_chart: ft.LineChart | None = None
        self.api_status_texts: dict[str, ft.Text] = {}
        self.test_button: ft.ElevatedButton | None = None
        self.status_text: ft.Text | None = None

    def build(self) -> None:
        """ウィジェットの構築"""
        # タイトル
        title = ft.Text(
            "英会話能力測定AIアプリ",
            size=32,
            weight=ft.FontWeight.BOLD,
            text_align=ft.TextAlign.CENTER,
            color=ft.colors.BLACK
        )
        
        # 説明文
        description = ft.Text(
            "AIとリアルタイムで英会話を行い、あなたの英会話能力を測定します。\n"
            "発音、文法、流暢さなど、総合的な評価を提供します。",
            size=16,
            text_align=ft.TextAlign.CENTER,
            color=ft.colors.BLACK
        )
        
        # マイクとスピーカーのチェックセクション
        audio_section = self._create_audio_section()
        
        # APIチェックセクション
        api_section = self._create_api_section()
        
        # 開始ボタン
        start_button = ft.ElevatedButton(
            "測定を開始する",
            on_click=self._on_start_clicked,
            style=ft.ButtonStyle(
                padding=20,
            ),
            width=300,
            height=50
        )
        
        # レイアウト
        self.page.add(
            ft.Container(
                content=ft.Column(
                    [
                        ft.Container(height=20),
                        title,
                        ft.Container(height=10),
                        description,
                        ft.Container(height=20),
                        api_section,
                        ft.Container(height=20),
                        audio_section,
                        ft.Container(height=20),
                        ft.Row([start_button], alignment=ft.MainAxisAlignment.CENTER),
                        ft.Container(height=20),
                    ],
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    spacing=0,
                    scroll=ft.ScrollMode.AUTO,
                ),
                padding=40,
                expand=True,
            )
        )
        
        # 初期化処理
        self._check_apis()
        # リアルタイム波形表示を開始
        self._start_realtime_monitoring()
    
    def _create_audio_section(self) -> ft.Container:
        """音声チェックセクションの作成"""
        # マイク波形チャート
        self.mic_chart = ft.LineChart(
            data_series=[
                ft.LineChartData(
                    data_points=[],
                    stroke_width=2,
                    color=ft.colors.BLUE,
                    below_line_bgcolor=ft.colors.BLUE_100,
                )
            ],
            border=ft.border.Border(
                bottom=ft.BorderSide(4, ft.colors.with_opacity(0.5, ft.colors.ON_SURFACE)),
                left=ft.BorderSide(4, ft.colors.with_opacity(0.5, ft.colors.ON_SURFACE)),
                top=ft.BorderSide(4, ft.colors.with_opacity(0.5, ft.colors.ON_SURFACE)),
                right=ft.BorderSide(4, ft.colors.with_opacity(0.5, ft.colors.ON_SURFACE)),
            ),
            left_axis=ft.ChartAxis(
                labels_size=40,
            ),
            bottom_axis=ft.ChartAxis(
                labels_size=40,
            ),
            tooltip_bgcolor=ft.colors.with_opacity(0.8, ft.colors.BLUE_GREY),
            min_y=0.0,
            max_y=1.0,
            min_x=0,
            max_x=100,
            height=150,
            width=350,
        )
        
        # スピーカー波形チャート
        self.speaker_chart = ft.LineChart(
            data_series=[
                ft.LineChartData(
                    data_points=[],
                    stroke_width=2,
                    color=ft.colors.GREEN,
                    below_line_bgcolor=ft.colors.GREEN_100,
                )
            ],
            border=ft.border.Border(
                bottom=ft.BorderSide(4, ft.colors.with_opacity(0.5, ft.colors.ON_SURFACE)),
                left=ft.BorderSide(4, ft.colors.with_opacity(0.5, ft.colors.ON_SURFACE)),
                top=ft.BorderSide(4, ft.colors.with_opacity(0.5, ft.colors.ON_SURFACE)),
                right=ft.BorderSide(4, ft.colors.with_opacity(0.5, ft.colors.ON_SURFACE)),
            ),
            left_axis=ft.ChartAxis(
                labels_size=40,
            ),
            bottom_axis=ft.ChartAxis(
                labels_size=40,
            ),
            tooltip_bgcolor=ft.colors.with_opacity(0.8, ft.colors.BLUE_GREY),
            min_y=0.0,
            max_y=1.0,
            min_x=0,
            max_x=100,
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
            color=ft.colors.BLACK,
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
                        color=ft.colors.BLACK
                    ),
                    ft.Container(height=10),
                    ft.Row(
                        [
                            ft.Column(
                                [
                                    ft.Text("マイク", size=16, weight=ft.FontWeight.BOLD, color=ft.colors.BLACK),
                                    self.mic_chart,
                                ],
                                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                            ),
                            ft.Container(width=20),
                            ft.Column(
                                [
                                    ft.Text("スピーカー", size=16, weight=ft.FontWeight.BOLD, color=ft.colors.BLACK),
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
            border=ft.border.all(1, ft.colors.GREY_400),
            border_radius=10,
        )
    
    def _create_api_section(self) -> ft.Container:
        """APIチェックセクションの作成"""
        # API状態表示用のテキストを初期化
        api_results = self.api_check_service.check_all_apis()
        
        api_status_widgets = []
        for api_result in api_results:
            status_text = ft.Text(
                f"{api_result['name']}の状態：{api_result['status']}",
                size=14,
                color=ft.colors.BLACK
            )
            self.api_status_texts[api_result['name']] = status_text
            api_status_widgets.append(status_text)
        
        return ft.Container(
            content=ft.Column(
                [
                    ft.Text(
                        "LLM APIチェック",
                        size=20,
                        weight=ft.FontWeight.BOLD,
                        text_align=ft.TextAlign.CENTER,
                        color=ft.colors.BLACK
                    ),
                    ft.Container(height=10),
                    *api_status_widgets,
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            padding=20,
            border=ft.border.all(1, ft.colors.GREY_400),
            border_radius=10,
        )
    
    def _on_test_button_clicked(self, e: ft.ControlEvent) -> None:
        """テストボタンがクリックされたときの処理"""
        if self.is_recording:
            return
        
        def test_audio():
            """録音→再生のテスト処理"""
            try:
                # リアルタイム監視は停止せず、そのまま継続
                # record_audioは別のストリームを使用するため、リアルタイム監視と競合しない
                
                self.is_recording = True
                if self.status_text:
                    self.status_text.value = "録音中...「Hello」と発話してください（3秒間）"
                    self.status_text.color = ft.colors.BLUE
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
                        self.status_text.color = ft.colors.GREEN
                    self.page.update()
                    
                    # 再生（音量ゲイン10倍で再生）
                    volume_gain = 10.0
                    self.audio_service.play_audio(audio_data, volume_gain=volume_gain)
                    
                    # 再生波形を表示（増幅後のデータを表示）
                    amplified_audio_list = (np.array(audio_list) * volume_gain).tolist()
                    # クリッピングを防ぐため-1.0～1.0の範囲に制限
                    amplified_audio_list = [max(-1.0, min(1.0, x)) for x in amplified_audio_list]
                    self._update_speaker_waveform(amplified_audio_list)
                    
                    if self.status_text:
                        self.status_text.value = "テスト完了！マイクとスピーカーが正常に動作しています。"
                        self.status_text.color = ft.colors.GREEN
                else:
                    if self.status_text:
                        self.status_text.value = "録音に失敗しました。マイクの接続を確認してください。"
                        self.status_text.color = ft.colors.RED
                
                if self.test_button:
                    self.test_button.disabled = False
                self.page.update()
                
            except Exception as ex:
                print(f"テストエラー: {str(ex)}")
                if self.status_text:
                    self.status_text.value = f"エラーが発生しました: {str(ex)}"
                    self.status_text.color = ft.colors.RED
                if self.test_button:
                    self.test_button.disabled = False
                self.page.update()
            finally:
                self.is_recording = False
        
        # 別スレッドで実行
        test_thread = threading.Thread(target=test_audio, daemon=True)
        test_thread.start()
    
    def _update_mic_waveform(self, audio_data: list[float] | None) -> None:
        """マイク波形の更新（録音後）"""
        if not self.mic_chart or not audio_data:
            return
        
        try:
            # データをサンプリングして表示
            data_length = len(audio_data)
            if data_length > 0:
                # より多くのポイントを表示（200ポイント）
                step = max(1, data_length // self.max_buffer_size)
                mic_points = []
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
                speaker_points = []
                for i in range(0, min(data_length, self.max_buffer_size * step), step):
                    x = i // step
                    # 振幅の絶対値を使用（0から1の範囲）
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
    
    def _start_realtime_monitoring(self) -> None:
        """リアルタイム波形監視を開始"""
        # マイクの監視を開始
        self.audio_service.start_mic_monitoring(self._on_mic_data_received)
    
    def _on_mic_data_received(self, audio_data: list[float]) -> None:
        """マイクデータ受信時のコールバック"""
        try:
            # RMS値（実効値）を計算して波形の強度を取得
            if len(audio_data) > 0:
                np_data = np.array(audio_data)
                rms = np.sqrt(np.mean(np_data ** 2))
                # ピーク値も取得
                peak = np.max(np.abs(np_data))
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
                # 波形を更新（UIスレッドで実行）
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
            print(f"リアルタイム波形更新エラー: {str(e)}")
    
    def _check_apis(self) -> None:
        """APIの状態をチェック"""
        api_results = self.api_check_service.check_all_apis()
        
        for api_result in api_results:
            if api_result['name'] in self.api_status_texts:
                status_text = self.api_status_texts[api_result['name']]
                status_text.value = f"{api_result['name']}の状態：{api_result['status']}"
                
                # 状態に応じて色を変更
                if api_result['status'] == "利用可能":
                    status_text.color = ft.colors.GREEN
                elif api_result['status'] == "エラー":
                    status_text.color = ft.colors.RED
                else:
                    status_text.color = ft.colors.ORANGE
        
        self.page.update()
    
    def _on_start_clicked(self, e: ft.ControlEvent) -> None:
        """開始ボタンがクリックされたときの処理"""
        if self.on_start_callback:
            self.on_start_callback()
        else:
            print("測定を開始します")
