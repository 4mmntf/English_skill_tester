# テスト作成ガイド

## 概要

このプロジェクトでは、すべての新機能に対してテストを作成し、テストカバレッジを維持することが求められます。

## テスト作成の基本原則

### 1. テスト駆動開発（TDD）

新しい機能を追加する際は、以下の順序で進めます：

1. **テストを書く** - 期待される動作をテストとして記述
2. **テストを実行** - テストが失敗することを確認（Red）
3. **実装を追加** - 最小限の実装でテストを通す
4. **リファクタリング** - コードを改善し、テストが通ることを確認（Green）

### 2. テストカバレッジ目標

- **新規コード**: 最低80%のカバレッジ
- **重要な機能**: 100%のカバレッジ
- **全体**: 現在32%、目標は60%以上

### 3. テストの種類

#### 単体テスト（Unit Tests）

個々の関数やメソッドをテストします。

```python
def test_save_evaluation_data_success(self, storage_service):
    """評価データの保存成功テスト"""
    data = {"test": "data", "score": 85}
    result = storage_service.save_evaluation_data(data, "test.json")
    assert result is True
```

#### 統合テスト（Integration Tests）

複数のコンポーネントが連携して動作することをテストします。

```python
@pytest.mark.asyncio
async def test_evaluate_conversation_with_azure(self, evaluation_service_with_azure):
    """Azureありで会話評価を実行"""
    # OpenAIとAzureの両方が動作することを確認
    result = await evaluation_service_with_azure.evaluate_conversation(...)
    assert isinstance(result, EvaluationResult)
```

#### モックとフィクスチャ

外部依存（API、ファイルシステムなど）をモック化します。

```python
@patch('app.services.openai_service.OpenAI')
def test_evaluate_conversation_success(self, mock_openai):
    """会話評価成功のテスト"""
    # OpenAI APIをモック化
    mock_client = Mock()
    mock_openai.return_value = mock_client
    # テスト実行
```

## テストファイルの構造

### ファイル名

- テストファイル: `test_<module_name>.py`
- 例: `test_storage_service.py`, `test_conversation_window.py`

### クラス名

- テストクラス: `Test<ClassName>`
- 例: `TestLocalStorageService`, `TestConversationWindow`

### メソッド名

- テストメソッド: `test_<method_name>_<scenario>`
- 例: `test_save_evaluation_data_success`, `test_save_evaluation_data_failure`

## テストの書き方

### 基本的なテスト構造

```python
class TestMyService:
    """MyServiceのテストクラス"""
    
    @pytest.fixture
    def my_service(self):
        """MyServiceのインスタンスを作成"""
        return MyService()
    
    def test_method_success(self, my_service):
        """成功ケースのテスト"""
        # Arrange（準備）
        input_data = {"key": "value"}
        
        # Act（実行）
        result = my_service.method(input_data)
        
        # Assert（検証）
        assert result is not None
        assert result["key"] == "value"
    
    def test_method_failure(self, my_service):
        """失敗ケースのテスト"""
        # Arrange
        invalid_data = None
        
        # Act & Assert
        with pytest.raises(ValueError):
            my_service.method(invalid_data)
```

### 非同期テスト

```python
@pytest.mark.asyncio
async def test_async_method(self, my_service):
    """非同期メソッドのテスト"""
    result = await my_service.async_method()
    assert result is not None
```

### モックの使用

```python
@patch('app.services.external_api.ExternalAPI')
def test_method_with_external_api(self, mock_api):
    """外部APIを使用するメソッドのテスト"""
    # モックの設定
    mock_api.return_value.get_data.return_value = {"data": "test"}
    
    # テスト実行
    service = MyService()
    result = service.method_using_api()
    
    # 検証
    assert result == {"data": "test"}
    mock_api.return_value.get_data.assert_called_once()
```

### フィクスチャの使用

```python
@pytest.fixture
def temp_data_dir(self):
    """一時的なデータディレクトリを作成"""
    temp_dir = Path(tempfile.mkdtemp())
    yield temp_dir
    shutil.rmtree(temp_dir)  # クリーンアップ

def test_with_temp_dir(self, temp_data_dir):
    """一時ディレクトリを使用するテスト"""
    file_path = temp_data_dir / "test.txt"
    file_path.write_text("test")
    assert file_path.exists()
```

## テスト実行

### すべてのテストを実行

```bash
uv run pytest tests/ -v
```

### カバレッジ付きで実行

```bash
uv run pytest tests/ --cov=app --cov-report=term-missing --cov-report=html
```

### 特定のテストを実行

```bash
# 特定のファイル
uv run pytest tests/test_storage_service.py -v

# 特定のクラス
uv run pytest tests/test_storage_service.py::TestLocalStorageService -v

# 特定のメソッド
uv run pytest tests/test_storage_service.py::TestLocalStorageService::test_save_evaluation_data_success -v
```

### カバレッジレポートの確認

```bash
# HTMLレポートを開く
open htmlcov/index.html
```

## よくあるテストパターン

### 1. 成功ケースと失敗ケース

```python
def test_save_data_success(self, service):
    """保存成功のテスト"""
    result = service.save_data({"key": "value"})
    assert result is True

def test_save_data_failure(self, service):
    """保存失敗のテスト"""
    with patch('builtins.open', side_effect=PermissionError()):
        result = service.save_data({"key": "value"})
        assert result is False
```

### 2. エッジケース

```python
def test_save_data_empty(self, service):
    """空データの保存テスト"""
    result = service.save_data({})
    assert result is True

def test_save_data_none(self, service):
    """Noneデータの保存テスト"""
    with pytest.raises(ValueError):
        service.save_data(None)
```

### 3. 状態の変化を確認

```python
def test_start_monitoring(self, service):
    """監視開始のテスト"""
    assert service.is_recording is False
    service.start_monitoring()
    assert service.is_recording is True
```

## ベストプラクティス

1. **テストは独立させる**
   - テスト間で状態を共有しない
   - 各テストは独立して実行できるようにする

2. **明確なアサーション**
   - 何をテストしているか明確にする
   - エラーメッセージが分かりやすいようにする

3. **テストデータの管理**
   - フィクスチャを使用してテストデータを管理
   - 一時ファイルやディレクトリは適切にクリーンアップ

4. **モックの適切な使用**
   - 外部依存をモック化
   - モックの動作を明確に定義

5. **テストの命名**
   - テスト名から何をテストしているか分かるようにする
   - `test_<method>_<scenario>`の形式を守る

## トラブルシューティング

### テストが失敗する場合

1. **エラーメッセージを確認**
   ```bash
   uv run pytest tests/ -v --tb=short
   ```

2. **特定のテストのみ実行**
   ```bash
   uv run pytest tests/test_specific.py::test_specific_method -v
   ```

3. **デバッグモードで実行**
   ```bash
   uv run pytest tests/ -v --pdb
   ```

### カバレッジが低い場合

1. **カバレッジレポートを確認**
   ```bash
   open htmlcov/index.html
   ```

2. **未カバーの行を確認**
   - HTMLレポートで赤く表示されている行を確認
   - それらの行に対するテストを追加

## 参考資料

- [pytest公式ドキュメント](https://docs.pytest.org/)
- [pytest fixtures](https://docs.pytest.org/en/stable/fixture.html)
- [pytest mocking](https://docs.pytest.org/en/stable/monkeypatch.html)
- [coverage公式ドキュメント](https://coverage.readthedocs.io/)

