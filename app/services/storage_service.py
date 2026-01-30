"""
ローカルストレージサービス
ユーザー認証不要で、ローカルファイルにデータを保存する
"""
import os
import json
from typing import Dict, List, Any
from pathlib import Path
from datetime import datetime
from app.config import APP_DATA_DIR


class LocalStorageService:
    """ローカルファイルに評価データを保存・読み込むサービスクラス"""
    
    def __init__(self) -> None:
        """
        初期化処理
        データ保存ディレクトリを作成する
        """
        # データ保存ディレクトリ
        self.data_dir: Path = APP_DATA_DIR / "evaluations"
        self.data_dir.mkdir(parents=True, exist_ok=True)

    def save_evaluation_data(self, data: Dict[str, Any], filename: str | None = None) -> bool:
        """
        評価データをローカルファイルに保存
        
        Args:
            data: 保存するデータ（辞書形式）
            filename: ファイル名（指定しない場合はタイムスタンプから自動生成）
        
        Returns:
            保存成功時True、失敗時False
        """
        try:
            # ファイル名が指定されていない場合はタイムスタンプから生成
            if not filename:
                timestamp: str = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"evaluation_{timestamp}.json"
            
            # ファイルパス
            file_path: Path = self.data_dir / filename
            
            # JSON形式で保存
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            return True
        except Exception as e:
            print(f"評価データの保存に失敗しました: {str(e)}")
            return False

    def list_evaluation_history(self) -> List[Dict[str, Any]]:
        """
        ローカルファイルから評価履歴のリストを取得
        
        Returns:
            評価履歴のリスト（ファイル名、パス、更新日時、サイズを含む辞書のリスト）
        """
        try:
            history: List[Dict[str, Any]] = []
            # データディレクトリ内のすべてのJSONファイルを取得
            for file_path in self.data_dir.glob("*.json"):
                try:
                    # ファイルのメタデータを取得
                    stat = file_path.stat()
                    history.append({
                        "filename": file_path.name,
                        "path": str(file_path),
                        "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                        "size": stat.st_size
                    })
                except Exception as e:
                    print(f"ファイルの読み込みに失敗しました {file_path}: {str(e)}")
            
            # 更新日時でソート（新しい順）
            history.sort(key=lambda x: x["modified"], reverse=True)
            return history
        except Exception as e:
            print(f"評価履歴の取得に失敗しました: {str(e)}")
            return []
    
    def load_evaluation_data(self, filename: str) -> Dict[str, Any] | None:
        """
        評価データをローカルファイルから読み込む
        
        Args:
            filename: ファイル名
        
        Returns:
            評価データ（辞書形式）、読み込み失敗時はNone
        """
        try:
            file_path: Path = self.data_dir / filename
            if not file_path.exists():
                return None
            
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"評価データの読み込みに失敗しました: {str(e)}")
            return None
    
    def save_test_progress(self, test_id: str, progress_data: Dict[str, Any]) -> bool:
        """
        テストの進捗状況を保存
        
        Args:
            test_id: テストID（pronunciation, conversation, listening, grammar）
            progress_data: 進捗データ（辞書形式）
        
        Returns:
            保存成功時True、失敗時False
        """
        try:
            # テスト進捗保存ディレクトリ
            progress_dir: Path = APP_DATA_DIR / "test_progress"
            progress_dir.mkdir(parents=True, exist_ok=True)
            
            # ファイルパス
            file_path: Path = progress_dir / f"{test_id}_progress.json"
            
            # JSON形式で保存
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(progress_data, f, ensure_ascii=False, indent=2)
            
            return True
        except Exception as e:
            print(f"テスト進捗の保存に失敗しました: {str(e)}")
            return False
    
    def load_test_progress(self, test_id: str) -> Dict[str, Any] | None:
        """
        テストの進捗状況を読み込む
        
        Args:
            test_id: テストID（pronunciation, conversation, listening, grammar）
        
        Returns:
            進捗データ（辞書形式）、読み込み失敗時はNone
        """
        try:
            progress_dir: Path = APP_DATA_DIR / "test_progress"
            file_path: Path = progress_dir / f"{test_id}_progress.json"
            
            if not file_path.exists():
                return None
            
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"テスト進捗の読み込みに失敗しました: {str(e)}")
            return None
    
    def delete_test_progress(self, test_id: str | None = None) -> bool:
        """
        テストの進捗状況を削除
        
        Args:
            test_id: テストID（指定しない場合はすべてのテスト進捗を削除）
        
        Returns:
            削除成功時True、失敗時False
        """
        try:
            progress_dir: Path = APP_DATA_DIR / "test_progress"
            
            if test_id:
                # 特定のテストの進捗を削除
                file_path: Path = progress_dir / f"{test_id}_progress.json"
                if file_path.exists():
                    file_path.unlink()
            else:
                # すべてのテスト進捗を削除
                for file_path in progress_dir.glob("*_progress.json"):
                    file_path.unlink()
            
            return True
        except Exception as e:
            print(f"テスト進捗の削除に失敗しました: {str(e)}")
            return False
    
    def has_test_progress(self) -> bool:
        """
        テストの進捗状況が存在するか確認
        
        Returns:
            進捗が存在する場合True、存在しない場合False
        """
        try:
            progress_dir: Path = APP_DATA_DIR / "test_progress"
            return any(progress_dir.glob("*_progress.json"))
        except Exception:
            return False

