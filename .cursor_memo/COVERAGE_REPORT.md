# テストカバレッジレポート

## 概要

このプロジェクトでは、pytestとcoverageを使用してテストカバレッジを測定しています。

## 現在のカバレッジ状況

### 全体カバレッジ: **32%**

### モジュール別カバレッジ

| モジュール | カバレッジ | 状態 |
|-----------|-----------|------|
| `app/services/evaluation_service.py` | **100%** | ✅ 完全 |
| `app/services/openai_service.py` | **97%** | ✅ 良好 |
| `app/services/api_check_service.py` | **95%** | ✅ 良好 |
| `app/services/audio_service.py` | **81%** | ✅ 良好 |
| `app/services/storage_service.py` | **80%** | ✅ 良好 |
| `app/models/schemas.py` | **100%** | ✅ 完全 |
| `app/config.py` | **64%** | ⚠️ 要改善 |
| `app/services/azure_service.py` | **41%** | ⚠️ 要改善 |
| `app/gui/conversation_window.py` | **26%** | ⚠️ 要改善 |
| `app/services/realtime_service.py` | **6%** | ❌ 要改善 |
| `app/gui/home_window.py` | **8%** | ❌ 要改善 |
| `app/main.py` | **47%** | ⚠️ 要改善 |

## テストファイル

### サービス層のテスト

- ✅ `tests/test_storage_service.py` - LocalStorageServiceのテスト（15テスト）
- ✅ `tests/test_api_check_service.py` - APICheckServiceのテスト（8テスト）
- ✅ `tests/test_openai_service.py` - OpenAIServiceのテスト（6テスト）
- ✅ `tests/test_evaluation_service.py` - EvaluationServiceのテスト（3テスト）
- ✅ `tests/test_audio_service.py` - AudioServiceのテスト（12テスト）

### GUI層のテスト

- ✅ `tests/test_conversation_window.py` - ConversationWindowの基本テスト（5テスト）
- ✅ `tests/test_conversation_window_methods.py` - ConversationWindowのメソッドテスト（8テスト）

### インポートテスト

- ✅ `tests/test_imports.py` - 基本的なインポートテスト

## カバレッジレポートの表示

### HTMLレポート

```bash
# HTMLレポートを生成（既に生成済み）
open htmlcov/index.html
```

### ターミナルレポート

```bash
# カバレッジ付きでテストを実行
uv run pytest tests/ --cov=app --cov-report=term-missing
```

### XMLレポート

```bash
# XMLレポートを生成（CI/CD用）
uv run pytest tests/ --cov=app --cov-report=xml
```

## テスト実行方法

### すべてのテストを実行

```bash
uv run pytest tests/ -v
```

### カバレッジ付きでテストを実行

```bash
uv run pytest tests/ --cov=app --cov-report=term-missing --cov-report=html
```

### 特定のテストファイルを実行

```bash
uv run pytest tests/test_storage_service.py -v
```

### 特定のテストクラスを実行

```bash
uv run pytest tests/test_storage_service.py::TestLocalStorageService -v
```

## 今後の改善点

### 優先度: 高

1. **RealtimeServiceのテスト追加** (現在6%)
   - 接続/切断のテスト
   - イベントハンドリングのテスト
   - エラーハンドリングのテスト

2. **ConversationWindowのテスト拡充** (現在26%)
   - UIイベントハンドリングのテスト
   - タイマー機能のテスト
   - 会話テストの統合テスト

### 優先度: 中

3. **AzureServiceのテスト追加** (現在41%)
   - 発音評価のテスト
   - エラーハンドリングのテスト

4. **HomeWindowのテスト追加** (現在8%)
   - UIコンポーネントのテスト
   - イベントハンドリングのテスト

### 優先度: 低

5. **Mainモジュールのテスト追加** (現在47%)
   - アプリケーション初期化のテスト
   - 画面遷移のテスト

## テスト作成ガイドライン

### 新しい機能を追加する際

1. **機能実装前にテストを書く（TDD）**
   - まずテストを書く
   - テストが失敗することを確認
   - 実装を追加
   - テストが成功することを確認

2. **テストカバレッジを維持**
   - 新しいコードに対しては最低80%のカバレッジを目指す
   - 重要な機能は100%のカバレッジを目指す

3. **テストの命名規則**
   - テストファイル: `test_<module_name>.py`
   - テストクラス: `Test<ClassName>`
   - テストメソッド: `test_<method_name>_<scenario>`

4. **テストの構造**
   ```python
   def test_method_name_success(self, fixture):
       """成功ケースのテスト"""
       # Arrange
       # Act
       # Assert
   ```

## CI/CD統合

### GitHub Actionsでの実行例

```yaml
- name: Run tests with coverage
  run: |
    uv run pytest tests/ --cov=app --cov-report=xml --cov-report=term
```

### カバレッジ閾値の設定

`pytest.ini`でカバレッジの閾値を設定できます：

```ini
[pytest]
# カバレッジ閾値（オプション）
# --cov-fail-under=80
```

## 参考資料

- [pytest公式ドキュメント](https://docs.pytest.org/)
- [coverage公式ドキュメント](https://coverage.readthedocs.io/)
- [pytest-cov公式ドキュメント](https://pytest-cov.readthedocs.io/)

