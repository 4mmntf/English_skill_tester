"""
AudioServiceのテスト
"""
import pytest
import numpy as np
from unittest.mock import patch, Mock, MagicMock
from app.services.audio_service import AudioService


class TestAudioService:
    """AudioServiceのテストクラス"""
    
    @pytest.fixture
    def audio_service(self):
        """AudioServiceのインスタンスを作成"""
        return AudioService()
    
    def test_init(self, audio_service):
        """初期化テスト"""
        assert audio_service.is_recording is False
        assert audio_service.is_playing is False
        assert audio_service.chunk_size == 1024
        assert audio_service.sample_rate == 44100
        assert audio_service.channels == 1
    
    @patch('app.services.audio_service.sd.query_devices')
    def test_get_audio_devices(self, mock_query_devices, audio_service):
        """音声デバイス取得のテスト"""
        # モックデバイスデータ
        mock_devices = [
            {'name': 'Input Device', 'max_input_channels': 2, 'max_output_channels': 0},
            {'name': 'Output Device', 'max_input_channels': 0, 'max_output_channels': 2},
            {'name': 'Both Device', 'max_input_channels': 2, 'max_output_channels': 2},
        ]
        mock_query_devices.return_value = mock_devices
        
        with patch('app.services.audio_service.sd.query_devices') as mock_query:
            # query_devicesの呼び出しをモック
            def query_side_effect(kind=None):
                if kind == 'input':
                    return [mock_devices[0]]
                elif kind == 'output':
                    return [mock_devices[1]]
                else:
                    return mock_devices
            
            mock_query.side_effect = query_side_effect
            devices = audio_service.get_audio_devices()
        
        assert 'input_devices' in devices
        assert 'output_devices' in devices
        assert 'default_input' in devices
        assert 'default_output' in devices
    
    def test_start_mic_monitoring(self, audio_service):
        """マイク監視開始のテスト"""
        callback = Mock()
        
        with patch('threading.Thread') as mock_thread:
            result = audio_service.start_mic_monitoring(callback)
            
            assert result is True
            assert audio_service.is_recording is True
            assert audio_service.mic_callback == callback
            assert mock_thread.called
    
    def test_start_mic_monitoring_already_recording(self, audio_service):
        """既に録音中の場合は開始しない"""
        audio_service.is_recording = True
        callback = Mock()
        
        result = audio_service.start_mic_monitoring(callback)
        
        assert result is False
    
    def test_stop_mic_monitoring(self, audio_service):
        """マイク監視停止のテスト"""
        audio_service.is_recording = True
        mock_thread = Mock()
        audio_service.recording_thread = mock_thread
        
        audio_service.stop_mic_monitoring()
        
        assert audio_service.is_recording is False
        assert audio_service.mic_callback is None
    
    def test_start_speaker_monitoring(self, audio_service):
        """スピーカー監視開始のテスト"""
        callback = Mock()
        
        with patch('threading.Thread') as mock_thread:
            result = audio_service.start_speaker_monitoring(callback)
            
            assert result is True
            assert audio_service.is_playing is True
            assert audio_service.speaker_callback == callback
            assert mock_thread.called
    
    def test_start_speaker_monitoring_already_playing(self, audio_service):
        """既に再生中の場合は開始しない"""
        audio_service.is_playing = True
        callback = Mock()
        
        result = audio_service.start_speaker_monitoring(callback)
        
        assert result is False
    
    def test_stop_speaker_monitoring(self, audio_service):
        """スピーカー監視停止のテスト"""
        audio_service.is_playing = True
        mock_thread = Mock()
        audio_service.playing_thread = mock_thread
        
        audio_service.stop_speaker_monitoring()
        
        assert audio_service.is_playing is False
        assert audio_service.speaker_callback is None
    
    @patch('app.services.audio_service.sd.rec')
    @patch('app.services.audio_service.sd.wait')
    def test_record_audio(self, mock_wait, mock_rec, audio_service):
        """音声録音のテスト"""
        mock_audio_data = np.array([0.1, 0.2, 0.3], dtype=np.float32)
        mock_rec.return_value = mock_audio_data.reshape(-1, 1)
        
        result = audio_service.record_audio(duration=1.0)
        
        assert isinstance(result, np.ndarray)
        assert len(result) > 0
        assert mock_rec.called
        assert mock_wait.called
    
    @patch('app.services.audio_service.sd.rec')
    @patch('app.services.audio_service.sd.wait')
    def test_record_audio_error(self, mock_wait, mock_rec, audio_service):
        """録音エラーのテスト"""
        mock_rec.side_effect = Exception("Recording error")
        
        result = audio_service.record_audio(duration=1.0)
        
        assert isinstance(result, np.ndarray)
        assert len(result) == 0
    
    @patch('app.services.audio_service.sd.play')
    @patch('app.services.audio_service.sd.wait')
    def test_play_audio(self, mock_wait, mock_play, audio_service):
        """音声再生のテスト"""
        audio_data = np.array([0.1, 0.2, 0.3], dtype=np.float32)
        
        audio_service.play_audio(audio_data, volume_gain=2.0)
        
        assert mock_play.called
        assert mock_wait.called
    
    @patch('app.services.audio_service.sd.play')
    @patch('app.services.audio_service.sd.wait')
    def test_play_audio_error(self, mock_wait, mock_play, audio_service):
        """再生エラーのテスト"""
        mock_play.side_effect = Exception("Playback error")
        audio_data = np.array([0.1, 0.2, 0.3], dtype=np.float32)
        
        # エラーが発生しても例外を投げないことを確認
        try:
            audio_service.play_audio(audio_data)
        except Exception:
            pytest.fail("play_audio should not raise exceptions")

