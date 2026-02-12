"""
英会話能力測定AIアプリ - メインエントリーポイント
macOS開発環境、Windows配布
"""
import sys
import os
import flet as ft
from pathlib import Path
from app.gui.home_window import HomeWindow
from app.gui.conversation_window import ConversationWindow
from app.gui.result_window import ResultWindow
from app.gui.history_window import HistoryWindow
from app.config import APP_DATA_DIR

# 環境変数の読み込み
from dotenv import load_dotenv

# .envファイルの読み込み（実行ファイルのディレクトリまたはカレントディレクトリから）
if getattr(sys, 'frozen', False):
    # PyInstallerでビルドされた場合
    application_path = Path(sys.executable).parent
    
    # Fletクライアントの正しいパスを設定 (onedirモード)
    # PyInstallerはfletファイルを _internal/flet に配置する
    flet_path = application_path / '_internal' / 'flet'
    if flet_path.exists():
        # get_package_bin_dir()が正しいパスを返すようにモンキーパッチ
        import flet_desktop
        def patched_get_package_bin_dir():
            return str(flet_path.parent)
        flet_desktop.get_package_bin_dir = patched_get_package_bin_dir
        print(f"Flet client path set to: {flet_path.parent}")
else:
    # 開発環境の場合
    application_path = Path(__file__).parent.parent

env_path = application_path / ".env"
if env_path.exists():
    load_dotenv(env_path)
else:
    # ホームディレクトリやAppDataからも探す
    load_dotenv()

# APIキーが環境変数に設定されていない場合、埋め込みキーを使用（配布用）
# 注意: PyInstallerの--keyオプションでバイトコードを暗号化することを推奨



class App:
    """アプリケーションのメインクラス"""
    
    def __init__(self, page: ft.Page) -> None:
        """
        初期化処理
        
        Args:
            page: Fletのページオブジェクト
        """
        self.page = page
        self.page.title = "英会話能力測定AIアプリ"
        # 全画面表示に設定
        self.page.window_full_screen = True
        self.page.window_min_width = 1200  # 最小幅も設定
        self.page.window_min_height = 800   # 最小高さも設定
        self.page.theme_mode = ft.ThemeMode.LIGHT
        self.page.bgcolor = ft.colors.WHITE
        
        # アプリケーションデータディレクトリの作成
        APP_DATA_DIR.mkdir(parents=True, exist_ok=True)
        
        # 会話画面を直接表示（メイン画面タブが最初に表示される）
        self.show_conversation()
    
    def show_home(self) -> None:
        """ホーム画面を表示"""
        self.page.clean()
        home_window = HomeWindow(
            self.page,
            on_start_callback=self.show_conversation
        )
        home_window.build()
        # ウィンドウサイズの変更を反映（コンテンツ追加後に更新）
        self.page.update()
    
    def show_conversation(self) -> None:
        """会話画面を表示"""
        self.page.clean()
        conversation_window = ConversationWindow(self.page)
        conversation_window.build()
    
    def show_result(self) -> None:
        """結果画面を表示"""
        self.page.clean()
        result_window = ResultWindow(self.page)
        result_window.build()
    
    def show_history(self) -> None:
        """履歴画面を表示"""
        self.page.clean()
        history_window = HistoryWindow(self.page)
        history_window.build()


def main(page: ft.Page) -> None:
    """アプリケーションの起動"""
    app = App(page)


if __name__ == "__main__":
    ft.app(target=main, view=ft.AppView.FLET_APP)
