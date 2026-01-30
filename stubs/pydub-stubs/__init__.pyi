"""Type stubs for pydub package"""
from typing import Any

class AudioSegment:
    def __init__(self, data: Any, frame_rate: int = 44100, channels: int = 1, sample_width: int = 2) -> None: ...
    def export(self, out_f: str, format: str = "mp3", bitrate: str = "192k") -> None: ...

