# 非同期処理の改善計画

## 現状分析

### 現在の非同期処理の実装状況

#### ✅ 適切に非同期化されている部分

1. **OpenAIService.evaluate_conversation()** - `async def`で実装
2. **EvaluationService.evaluate_conversation()** - `async def`で実装
3. **AzureService.assess_pronunciation()** - `async def`で実装

#### ⚠️ 改善が必要な部分

1. **ConversationWindow._evaluate_conversation_async()**
   - 現在: `threading.Thread` + `asyncio.run()`を使用
   - 問題: 新しいイベントループを作成しているが、既存のイベントループと統合されていない
   - 改善: Fletの非同期機能を活用するか、適切なイベントループ管理を実装

2. **ConversationWindow._save_conversation_data()**
   - 現在: 同期的なファイルI/O（`open()`, `json.dump()`, `AudioSegment.export()`）
   - 問題: 大きなファイルの保存時にUIがブロックされる可能性
   - 改善: `aiofiles`を使用して非同期ファイルI/Oに変更

3. **RealtimeService**
   - 現在: `threading.Thread`を使用
   - 問題: イベントループが別スレッドで実行されている
   - 改善: `asyncio`ベースの実装に変更

4. **AudioService**
   - 現在: `threading.Thread`を使用
   - 問題: コールバックベースだが、非同期処理と統合されていない
   - 改善: `asyncio`ベースのストリーム処理に変更

## 改善提案

### 1. 評価処理の非同期化改善

**現在の実装:**
```python
def _evaluate_conversation_async(self, is_final: bool = False) -> None:
    def evaluate_thread():
        async def run_evaluation():
            return await self.evaluation_service.openai_service.evaluate_conversation(...)
        evaluation_result = asyncio.run(run_evaluation())  # 新しいイベントループ
```

**改善案:**
```python
async def _evaluate_conversation_async(self, is_final: bool = False) -> None:
    """会話を非同期で評価"""
    try:
        conversation_text = self._format_conversation_history()
        if not conversation_text:
            return
        
        # 既存のイベントループで実行（新しいループを作らない）
        evaluation_result = await self.evaluation_service.openai_service.evaluate_conversation(conversation_text)
        
        # UI更新はFletの非同期機能を使用
        # ...
    except Exception as e:
        # エラーハンドリング
```

### 2. ファイル保存の非同期化

**現在の実装:**
```python
def _save_conversation_data(self, ...) -> None:
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(json_data, f, ...)  # ブロッキングI/O
    audio_segment.export(...)  # ブロッキングI/O
```

**改善案:**
```python
async def _save_conversation_data_async(self, ...) -> None:
    """会話データを非同期で保存"""
    import aiofiles
    import asyncio
    
    # 非同期ファイル書き込み
    async with aiofiles.open(json_path, 'w', encoding='utf-8') as f:
        await f.write(json.dumps(json_data, ...))
    
    # MP3エクスポートは別スレッドで実行（pydubが非同期対応していないため）
    await asyncio.to_thread(audio_segment.export, ...)
```

### 3. RealtimeServiceの非同期化

**現在の実装:**
```python
def _setup_event_handlers(self) -> None:
    def event_loop():
        for event in self.session:  # ブロッキング
            self._handle_event(event)
    event_thread = threading.Thread(target=event_loop, daemon=True)
```

**改善案:**
```python
async def _setup_event_handlers_async(self) -> None:
    """イベントハンドラーを非同期で設定"""
    async for event in self.session:  # 非同期イテレータ
        await self._handle_event_async(event)

async def _handle_event_async(self, event: Any) -> None:
    """イベントを非同期で処理"""
    # 非同期処理
```

### 4. AudioServiceの非同期化

**現在の実装:**
```python
def start_mic_monitoring(self, callback):
    def _record_audio():
        with sd.InputStream(...):  # ブロッキング
            while self.is_recording:
                time.sleep(0.1)
    self.recording_thread = threading.Thread(target=_record_audio)
```

**改善案:**
```python
async def start_mic_monitoring_async(self, callback):
    """マイク監視を非同期で開始"""
    async def _record_audio_async():
        # asyncio対応の音声ストリーム処理
        # または、asyncio.to_thread()でラップ
        pass
    await _record_audio_async()
```

## 実装優先順位

### 優先度: 高

1. **ファイル保存の非同期化** (`_save_conversation_data`)
   - 影響: 大きなファイル保存時にUIがフリーズする可能性
   - 実装難易度: 中
   - 依存: `aiofiles`パッケージの追加

2. **評価処理のイベントループ管理改善**
   - 影響: 複数の評価が同時に実行される場合の競合
   - 実装難易度: 低
   - 依存: なし

### 優先度: 中

3. **RealtimeServiceの非同期化**
   - 影響: イベント処理の効率化
   - 実装難易度: 高
   - 依存: OpenAI Realtime APIの非同期対応確認

4. **AudioServiceの非同期化**
   - 影響: 音声処理の効率化
   - 実装難易度: 高
   - 依存: `sounddevice`の非同期対応確認

## 実装ガイドライン

### 非同期処理の原則

1. **ブロッキング操作を避ける**
   - ファイルI/O: `aiofiles`を使用
   - ネットワークI/O: `aiohttp`や`httpx`の非同期版を使用
   - CPU集約的処理: `asyncio.to_thread()`でラップ

2. **イベントループの管理**
   - 新しいイベントループを作成しない（`asyncio.run()`を避ける）
   - 既存のイベントループを使用
   - Fletの非同期機能を活用

3. **エラーハンドリング**
   - 非同期関数内での例外処理
   - `asyncio.gather()`で複数の非同期処理を管理

4. **リソース管理**
   - `async with`を使用してリソースを管理
   - クリーンアップ処理も非同期で実行

### コード例

```python
# ✅ 良い例: 非同期ファイルI/O
import aiofiles

async def save_data_async(data: dict, path: Path) -> None:
    async with aiofiles.open(path, 'w', encoding='utf-8') as f:
        await f.write(json.dumps(data, ensure_ascii=False, indent=2))

# ✅ 良い例: CPU集約的処理を別スレッドで実行
import asyncio

async def process_audio_async(audio_data: np.ndarray) -> np.ndarray:
    # CPU集約的な処理は別スレッドで実行
    return await asyncio.to_thread(process_audio_cpu_intensive, audio_data)

# ❌ 悪い例: ブロッキングI/O
def save_data(data: dict, path: Path) -> None:
    with open(path, 'w') as f:  # ブロッキング
        json.dump(data, f)

# ❌ 悪い例: 新しいイベントループを作成
def run_async_in_thread():
    asyncio.run(async_function())  # 新しいループを作成
```

## 依存パッケージの追加

```toml
[project]
dependencies = [
    # ... 既存の依存関係 ...
    "aiofiles>=23.2.0",  # 非同期ファイルI/O
]
```

## テスト

非同期処理のテストには`pytest-asyncio`を使用：

```python
@pytest.mark.asyncio
async def test_save_data_async(storage_service):
    """非同期データ保存のテスト"""
    data = {"test": "data"}
    await storage_service.save_data_async(data, path)
    assert path.exists()
```

## 参考資料

- [Python asyncio公式ドキュメント](https://docs.python.org/3/library/asyncio.html)
- [aiofiles公式ドキュメント](https://github.com/Tinche/aiofiles)
- [Flet非同期処理](https://flet.dev/docs/guides/python/async/)

