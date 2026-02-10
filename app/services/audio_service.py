"""
音声入力/出力サービス
マイクとスピーカーのチェック、音声波形の取得を行う
"""

import sounddevice as sd
import numpy as np
from typing import Optional, Callable, List
import threading
import time


class AudioService:
    """音声入力/出力を管理するサービスクラス"""

    def __init__(self) -> None:
        """初期化処理"""
        self.is_recording: bool = False
        self.is_playing: bool = False
        self.recording_thread: Optional[threading.Thread] = None
        self.playing_thread: Optional[threading.Thread] = None
        self.mic_callback: Optional[Callable[[List[float]], None]] = None
        self.speaker_callback: Optional[Callable[[List[float]], None]] = None

        # 音声設定
        self.chunk_size: int = 1024
        self.sample_rate: int = 44100
        self.channels: int = 1
        self.dtype: np.dtype = np.float32

    def get_audio_devices(self) -> dict:
        """
        利用可能な音声デバイスを取得

        Returns:
            入力デバイスと出力デバイスの情報を含む辞書
        """
        input_devices: List[dict] = []
        output_devices: List[dict] = []

        devices = sd.query_devices()

        for i, device in enumerate(devices):
            if device["max_input_channels"] > 0:
                input_devices.append(
                    {
                        "index": i,
                        "name": device["name"],
                        "channels": device["max_input_channels"],
                    }
                )
            if device["max_output_channels"] > 0:
                output_devices.append(
                    {
                        "index": i,
                        "name": device["name"],
                        "channels": device["max_output_channels"],
                    }
                )

        default_input = sd.query_devices(kind="input")
        default_output = sd.query_devices(kind="output")

        return {
            "input_devices": input_devices,
            "output_devices": output_devices,
            "default_input": default_input if len(default_input) > 0 else None,
            "default_output": default_output if len(default_output) > 0 else None,
        }

    def start_mic_monitoring(self, callback: Callable[[List[float]], None]) -> bool:
        """
        マイクの監視を開始

        Args:
            callback: 音声波形データを受け取るコールバック関数

        Returns:
            開始成功時True
        """
        if self.is_recording:
            return False

        self.mic_callback = callback
        self.is_recording = True
        self.recording_thread = threading.Thread(target=self._record_audio, daemon=True)
        self.recording_thread.start()
        return True

    def stop_mic_monitoring(self) -> None:
        """マイクの監視を停止"""
        self.is_recording = False
        if self.recording_thread:
            self.recording_thread.join(timeout=1.0)
        self.mic_callback = None

    def start_speaker_monitoring(self, callback: Callable[[List[float]], None]) -> bool:
        """
        スピーカーの監視を開始（ループバック）

        Args:
            callback: 音声波形データを受け取るコールバック関数

        Returns:
            開始成功時True
        """
        if self.is_playing:
            return False

        self.speaker_callback = callback
        self.is_playing = True
        self.playing_thread = threading.Thread(
            target=self._monitor_speaker, daemon=True
        )
        self.playing_thread.start()
        return True

    def stop_speaker_monitoring(self) -> None:
        """スピーカーの監視を停止"""
        self.is_playing = False
        if self.playing_thread:
            self.playing_thread.join(timeout=1.0)
        self.speaker_callback = None

    def _record_audio(self) -> None:
        """音声録音の内部処理"""

        def audio_callback(
            indata: np.ndarray, frames: int, time_info: dict, status: sd.CallbackFlags
        ) -> None:
            """sounddeviceのコールバック関数"""
            if status:
                print(f"Audio callback status: {status}")
            if self.mic_callback and self.is_recording:
                # 正規化されたデータをリストに変換
                audio_data = indata[:, 0] if indata.shape[1] > 0 else indata.flatten()
                self.mic_callback(audio_data.tolist())

        # 試行するデバイスのリストを作成
        candidate_devices = []

        # 1. デフォルトデバイス
        try:
            if sd.default.device[0] >= 0:
                candidate_devices.append(sd.default.device[0])
        except Exception:
            pass

        # 2. その他の入力可能なデバイス
        try:
            devices = sd.query_devices()
            for i, dev in enumerate(devices):
                if dev["max_input_channels"] > 0 and i not in candidate_devices:
                    candidate_devices.append(i)
        except Exception:
            pass

        # 最後にNoneを追加（デフォルトの挙動を試す）
        if None not in candidate_devices:
            candidate_devices.append(None)

        stream_opened = False
        last_error = None

        for device_index in candidate_devices:
            if not self.is_recording:
                break

            try:
                print(f"マイク監視を開始します (Device Index: {device_index})")
                with sd.InputStream(
                    samplerate=self.sample_rate,
                    channels=self.channels,
                    dtype=self.dtype,
                    blocksize=self.chunk_size,
                    callback=audio_callback,
                    device=device_index,
                ):
                    stream_opened = True
                    print(f"マイク監視中... (Device Index: {device_index})")
                    while self.is_recording:
                        time.sleep(0.1)

                # 正常に終了した場合はここでループを抜ける（エラーで終了した場合はexceptに行く）
                if not self.is_recording:
                    break

            except Exception as e:
                print(f"デバイス {device_index} でのエラー: {str(e)}")
                last_error = e
                # ループを継続して次のデバイスを試す
                if not self.is_recording:
                    break
                time.sleep(0.2)

        if not stream_opened and self.is_recording:
            print(
                f"すべてのデバイスでマイク監視に失敗しました。最後のエラー: {str(last_error)}"
            )
            self.is_recording = False

    def _monitor_speaker(self) -> None:
        """スピーカー監視の内部処理（ループバック）"""
        try:
            # ループバックデバイスを探す（プラットフォーム依存）
            # macOSでは通常利用できないため、ダミーデータを生成
            # WindowsではWASAPIループバックが利用可能

            while self.is_playing:
                # ダミーデータを生成（実際の実装ではループバックストリームを使用）
                dummy_data = [0.0] * self.chunk_size

                if self.speaker_callback:
                    self.speaker_callback(dummy_data)

                time.sleep(0.01)  # 10ms間隔
        except Exception as e:
            print(f"スピーカー監視エラー: {str(e)}")
            self.is_playing = False

    def record_audio(self, duration: float = 3.0) -> np.ndarray:
        """
        音声を録音する

        Args:
            duration: 録音時間（秒）

        Returns:
            録音された音声データ（numpy配列）
        """
        # 試行するデバイスのリストを作成
        candidate_devices = []
        try:
            if sd.default.device[0] >= 0:
                candidate_devices.append(sd.default.device[0])
        except Exception:
            pass
        try:
            devices = sd.query_devices()
            for i, dev in enumerate(devices):
                if dev["max_input_channels"] > 0 and i not in candidate_devices:
                    candidate_devices.append(i)
        except Exception:
            pass
        if None not in candidate_devices:
            candidate_devices.append(None)

        for device_index in candidate_devices:
            try:
                print(f"録音を開始します (Device Index: {device_index})")
                recording = sd.rec(
                    int(duration * self.sample_rate),
                    samplerate=self.sample_rate,
                    channels=self.channels,
                    dtype=self.dtype,
                    device=device_index,
                )
                sd.wait()  # 録音が完了するまで待機
                return recording.flatten()
            except Exception as e:
                print(f"録音エラー (Device {device_index}): {str(e)}")
                # 次のデバイスを試す
                continue

        print("すべてのデバイスで録音に失敗しました")
        return np.array([], dtype=self.dtype)

    def play_audio(
        self, audio_data: np.ndarray, volume_gain: float = 10.0
    ) -> Optional[np.ndarray]:
        """
        音声を再生する

        Args:
            audio_data: 再生する音声データ（numpy配列）
            volume_gain: 音量ゲイン（デフォルト10.0倍）

        Returns:
            再生された音声データ（増幅後）またはNone（失敗時）
        """
        # 音量ゲインを適用（クリッピングを防ぐため-1.0～1.0の範囲に制限）
        amplified = np.clip(audio_data * volume_gain, -1.0, 1.0)

        # 試行するデバイスのリストを作成
        candidate_devices = []

        # 1. デフォルトデバイス
        try:
            if sd.default.device[1] >= 0:  # Output default
                candidate_devices.append(sd.default.device[1])
        except Exception:
            pass

        # 2. その他の出力可能なデバイス
        try:
            devices = sd.query_devices()
            for i, dev in enumerate(devices):
                if dev["max_output_channels"] > 0 and i not in candidate_devices:
                    candidate_devices.append(i)
        except Exception:
            pass

        # 最後にNoneを追加（デフォルトの挙動を試す）
        if None not in candidate_devices:
            candidate_devices.append(None)

        for device_index in candidate_devices:
            try:
                print(f"再生を開始します (Device Index: {device_index})")
                sd.play(amplified, samplerate=self.sample_rate, device=device_index)
                sd.wait()  # 再生が完了するまで待機
                return amplified
            except Exception as e:
                print(f"再生エラー (Device {device_index}): {str(e)}")
                continue

        print("すべてのデバイスで再生に失敗しました")
        return None

    def __del__(self) -> None:
        """クリーンアップ"""
        self.stop_mic_monitoring()
        self.stop_speaker_monitoring()
