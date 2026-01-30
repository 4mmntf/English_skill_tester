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
            if device['max_input_channels'] > 0:
                input_devices.append({
                    'index': i,
                    'name': device['name'],
                    'channels': device['max_input_channels']
                })
            if device['max_output_channels'] > 0:
                output_devices.append({
                    'index': i,
                    'name': device['name'],
                    'channels': device['max_output_channels']
                })
        
        default_input = sd.query_devices(kind='input')
        default_output = sd.query_devices(kind='output')
        
        return {
            'input_devices': input_devices,
            'output_devices': output_devices,
            'default_input': default_input if len(default_input) > 0 else None,
            'default_output': default_output if len(default_output) > 0 else None
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
        self.playing_thread = threading.Thread(target=self._monitor_speaker, daemon=True)
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
        try:
            def audio_callback(indata: np.ndarray, frames: int, time_info: dict, status: sd.CallbackFlags) -> None:
                """sounddeviceのコールバック関数"""
                if self.mic_callback and self.is_recording:
                    # 正規化されたデータをリストに変換
                    audio_data = indata[:, 0] if indata.shape[1] > 0 else indata.flatten()
                    self.mic_callback(audio_data.tolist())
            
            with sd.InputStream(
                samplerate=self.sample_rate,
                channels=self.channels,
                dtype=self.dtype,
                blocksize=self.chunk_size,
                callback=audio_callback
            ):
                while self.is_recording:
                    time.sleep(0.1)
        except Exception as e:
            print(f"マイク監視エラー: {str(e)}")
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
        try:
            recording = sd.rec(
                int(duration * self.sample_rate),
                samplerate=self.sample_rate,
                channels=self.channels,
                dtype=self.dtype
            )
            sd.wait()  # 録音が完了するまで待機
            return recording.flatten()
        except Exception as e:
            print(f"録音エラー: {str(e)}")
            return np.array([], dtype=self.dtype)
    
    def play_audio(self, audio_data: np.ndarray, volume_gain: float = 10.0) -> None:
        """
        音声を再生する
        
        Args:
            audio_data: 再生する音声データ（numpy配列）
            volume_gain: 音量ゲイン（デフォルト10.0倍）
        """
        try:
            # 音量ゲインを適用（クリッピングを防ぐため-1.0～1.0の範囲に制限）
            amplified = np.clip(audio_data * volume_gain, -1.0, 1.0)
            sd.play(amplified, samplerate=self.sample_rate)
            sd.wait()  # 再生が完了するまで待機
        except Exception as e:
            print(f"再生エラー: {str(e)}")
    
    def __del__(self) -> None:
        """クリーンアップ"""
        self.stop_mic_monitoring()
        self.stop_speaker_monitoring()

