"""
アプリケーション設定
"""
import os
import sys
from pathlib import Path


def get_app_data_dir() -> Path:
    """
    アプリケーションのデータディレクトリを取得
    
    Returns:
        アプリケーションデータディレクトリのパス
    """
    if sys.platform == "win32":
        # Windowsの場合、AppData\Local\EnglishSkillAppを使用
        app_data: str | None = os.getenv("LOCALAPPDATA")
        if app_data:
            app_dir: Path = Path(app_data) / "EnglishSkillApp"
            app_dir.mkdir(exist_ok=True)
            return app_dir
    elif sys.platform == "darwin":
        # macOSの場合、~/Library/Application Support/EnglishSkillAppを使用
        app_support: Path = Path.home() / "Library" / "Application Support" / "EnglishSkillApp"
        app_support.mkdir(parents=True, exist_ok=True)
        return app_support
    # その他のOSまたはフォールバック
    return Path.home() / ".english_skill_app"


def get_config_file() -> Path:
    """
    設定ファイルのパスを取得
    
    Returns:
        設定ファイルのパス
    """
    return get_app_data_dir() / "config.json"


def get_log_file() -> Path:
    """
    ログファイルのパスを取得
    
    Returns:
        ログファイルのパス
    """
    return get_app_data_dir() / "app.log"


# アプリケーションデータディレクトリ
APP_DATA_DIR = get_app_data_dir()

# 設定ファイル
CONFIG_FILE = get_config_file()

# ログファイル
LOG_FILE = get_log_file()

