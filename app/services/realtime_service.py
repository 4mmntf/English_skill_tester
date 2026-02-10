"""
OpenAI Realtime APIサービス
"""

import os
import json
import base64
import threading
import time
from typing import Callable, Any, List, Dict
from openai import OpenAI


class RealtimeService:
    """OpenAI Realtime APIを使用するサービスクラス"""

    def __init__(self) -> None:
        """
        初期化処理
        環境変数からAPIキーを取得し、OpenAIクライアントを初期化する
        """
        api_key: str | None = os.getenv("OPENAI_API_KEY") or os.getenv("OPENAI_API")
        if not api_key:
            raise ValueError(
                "OPENAI_API_KEYまたはOPENAI_API環境変数が設定されていません"
            )
        self.client: OpenAI = OpenAI(api_key=api_key)

        # Realtime APIセッション
        self.session: Any | None = None
        self.connection_manager: Any | None = None  # コンテキストマネージャーを保存
        self.is_connected: bool = False

        # コールバック関数
        self.on_audio_received: Callable[[bytes], None] | None = None  # AI音声受信時
        self.on_text_received: Callable[[str], None] | None = None  # AIテキスト受信時
        self.on_student_transcript: Callable[[str], None] | None = (
            None  # 学生の転写受信時
        )
        self.on_error: Callable[[str], None] | None = None  # エラー時
        self.tool_handler: Callable[[str, Dict[str, Any]], str] | None = (
            None  # ツール実行ハンドラ
        )

        # 音声設定
        self.voice: str = "alloy"  # デフォルト音声
        self.model: str = "gpt-4o-realtime-preview-2024-12-17"

    def connect(
        self,
        system_prompt: str,
        voice: str = "alloy",
        tools: List[Dict[str, Any]] | None = None,
        tool_handler: Callable[[str, Dict[str, Any]], str] | None = None,
        on_audio_received: Callable[[bytes], None] | None = None,
        on_text_received: Callable[[str], None] | None = None,
        on_student_transcript: Callable[[str], None] | None = None,
        on_error: Callable[[str], None] | None = None,
    ) -> bool:
        """
        Realtime APIセッションを開始

        Args:
            system_prompt: システムプロンプト
            voice: 音声（"alloy", "echo", "fable", "onyx", "nova", "shimmer"）
            tools: ツール定義のリスト
            tool_handler: ツール実行時のコールバック関数
            on_audio_received: AI音声受信時のコールバック
            on_text_received: AIテキスト受信時のコールバック
            on_student_transcript: 学生の転写受信時のコールバック
            on_error: エラー時のコールバック

        Returns:
            接続成功時True、失敗時False
        """
        try:
            self.voice = voice
            self.tool_handler = tool_handler
            self.on_audio_received = on_audio_received
            self.on_text_received = on_text_received
            self.on_student_transcript = on_student_transcript
            self.on_error = on_error

            # Realtime APIセッションを作成（modelのみ）
            # RealtimeConnectionManagerはコンテキストマネージャーとして使用
            connection_manager = self.client.beta.realtime.connect(
                model=self.model,
            )

            # コンテキストマネージャーとして接続を開始
            # タイムアウトを避けるため、接続を確立するまで少し待機
            self.session = connection_manager.__enter__()

            # 接続が確立されるまで少し待機
            time.sleep(0.5)

            # セッション設定を送信（instructions、voice、音声フォーマットなど）
            if self.session:
                try:
                    # セッション設定を作成
                    session_config = {
                        "modalities": ["text", "audio"],
                        "instructions": system_prompt,
                        "voice": voice,
                        "input_audio_format": "pcm16",
                        "output_audio_format": "pcm16",
                        "input_audio_transcription": {"model": "whisper-1"},
                        "turn_detection": {
                            "type": "server_vad",  # サーバー側のVADを使用
                            "threshold": 0.5,  # 0.0-1.0の範囲。0.5は標準的。高すぎると小声が拾えないため、クライアント側のRMSフィルタとシステムプロンプトで制御する
                            "prefix_padding_ms": 300,  # 発話開始前に含めるパディング
                            "silence_duration_ms": 1000,  # 1000ms（1秒）無音が続いたら発話終了と判断（雑音での割り込み防止）
                        },
                        "temperature": 0.7,
                        "max_response_output_tokens": 1000,  # 音声が途切れないよう増やす
                    }

                    # ツールが指定されている場合は設定に追加
                    if tools:
                        session_config["tools"] = tools
                        session_config["tool_choice"] = "auto"

                    # セッション設定を更新
                    self.session.send(
                        {"type": "session.update", "session": session_config}
                    )
                except Exception as e:
                    print(f"セッション設定エラー: {str(e)}")
                    # セッション設定が失敗しても続行

            # イベントハンドラを設定
            self._setup_event_handlers()

            self.is_connected = True
            self.connection_manager = connection_manager  # 後で__exit__を呼ぶために保存
            return True

        except Exception as e:
            error_msg = f"Realtime API接続エラー: {str(e)}"
            if self.on_error:
                self.on_error(error_msg)
            print(error_msg)
            return False

    def _setup_event_handlers(self) -> None:
        """イベントハンドラを設定"""
        if not self.session:
            return

        # output_audio_bufferを定期的にチェックするスレッドを開始
        def check_audio_buffer():
            """output_audio_bufferを定期的にチェックして音声データを取得"""
            while self.is_connected and self.session:
                try:
                    # output_audio_bufferから音声データを取得
                    if (
                        hasattr(self.session, "output_audio_buffer")
                        and self.on_audio_received
                    ):
                        audio_buffer = self.session.output_audio_buffer
                        if audio_buffer and len(audio_buffer) > 0:
                            # バッファから音声データを取得
                            for audio_data in audio_buffer:
                                if audio_data and len(audio_data) > 0:
                                    self.on_audio_received(audio_data)
                            # バッファをクリア（必要に応じて）
                            # audio_buffer.clear()  # これは実装によって異なる可能性がある
                except Exception as e:
                    # エラーを無視して続行（バッファが利用できない場合など）
                    pass
                time.sleep(0.01)  # 10ms間隔でチェック

        # イベントループを別スレッドで実行
        def event_loop():
            try:
                # self.sessionがNoneでないことを確認してから反復処理
                current_session = self.session
                if current_session:
                    for event in current_session:
                        self._handle_event(event)
            except Exception as e:
                error_msg = f"Realtime APIイベントループエラー: {str(e)}"
                if self.on_error:
                    self.on_error(error_msg)
                print(error_msg)
                self.is_connected = False

        event_thread = threading.Thread(target=event_loop, daemon=True)
        event_thread.start()

        # 音声バッファチェックスレッドを開始
        audio_buffer_thread = threading.Thread(target=check_audio_buffer, daemon=True)
        audio_buffer_thread.start()

    def _handle_event(self, event: Any) -> None:
        """イベントを処理"""
        event_type = event.type if hasattr(event, "type") else None

        # デバッグ用：すべてのイベントタイプをログに出力
        if event_type:
            print(f"Realtime APIイベント: {event_type}")

        if event_type == "response.audio.delta":
            # AI音声データを受信
            if hasattr(event, "delta") and self.on_audio_received:
                try:
                    # base64デコード
                    audio_data = base64.b64decode(event.delta)
                    self.on_audio_received(audio_data)
                except Exception as e:
                    print(f"音声データデコードエラー: {str(e)}")

        elif event_type == "response.audio_transcript.delta":
            # AIテキストトランスクリプトを受信
            if hasattr(event, "delta") and self.on_text_received:
                self.on_text_received(event.delta)

        elif event_type == "response.output_item.added":
            # 出力アイテムが追加された
            if hasattr(event, "item") and hasattr(event.item, "type"):
                if event.item.type == "message" and hasattr(event.item, "content"):
                    # メッセージコンテンツを処理
                    for content_item in event.item.content:
                        if (
                            hasattr(content_item, "type")
                            and content_item.type == "audio"
                        ):
                            # 音声データがある場合
                            if (
                                hasattr(content_item, "audio")
                                and self.on_audio_received
                            ):
                                try:
                                    audio_data = base64.b64decode(content_item.audio)
                                    self.on_audio_received(audio_data)
                                except Exception as e:
                                    print(f"音声データデコードエラー: {str(e)}")

        elif event_type == "response.output_item.done":
            # 出力アイテムが完了した
            pass

        elif event_type == "conversation.item.input_audio_transcription.delta":
            # 学生の音声転写（デバッグ用）
            if hasattr(event, "delta"):
                print(f"学生音声転写: {event.delta}")

        elif event_type == "conversation.item.input_audio_transcription.completed":
            # 学生の音声転写完了
            if hasattr(event, "transcript") and self.on_student_transcript:
                transcript = event.transcript
                print(f"学生音声転写完了: {transcript}")
                self.on_student_transcript(transcript)

        elif event_type == "conversation.item.created":
            # 会話アイテムが作成された（学生の音声が認識された可能性）
            print(f"会話アイテム作成: conversation.item.created")

        elif event_type == "conversation.item.input_audio_buffer.speech_started":
            # 学生の音声検出開始
            print(
                "学生音声検出開始: conversation.item.input_audio_buffer.speech_started"
            )

        elif event_type == "conversation.item.input_audio_buffer.speech_stopped":
            # 学生の音声検出停止
            print(
                "学生音声検出停止: conversation.item.input_audio_buffer.speech_stopped"
            )

        elif event_type == "input_audio_buffer.speech_started":
            # 音声検出開始（デバッグ用）
            print("音声検出開始: input_audio_buffer.speech_started")

        elif event_type == "input_audio_buffer.speech_stopped":
            # 音声検出停止（デバッグ用）
            print("音声検出停止: input_audio_buffer.speech_stopped")

        elif event_type == "response.function_call_arguments.done":
            # 関数呼び出しの引数受信完了
            print(f"関数呼び出し引数完了: {event}")
            if (
                hasattr(event, "call_id")
                and hasattr(event, "name")
                and hasattr(event, "arguments")
            ):
                call_id = event.call_id
                name = event.name
                arguments = event.arguments

                # 別スレッドでツールを実行（音声処理をブロックしないため）
                threading.Thread(
                    target=self._execute_tool,
                    args=(call_id, name, arguments),
                    daemon=True,
                ).start()

        elif event_type == "error":
            # エラーイベント
            error_obj = getattr(event, "error", None)
            if error_obj:
                # Errorオブジェクトの場合
                if hasattr(error_obj, "message"):
                    error_msg = f"Realtime APIエラー: {error_obj.message}"
                elif hasattr(error_obj, "__str__"):
                    error_msg = f"Realtime APIエラー: {str(error_obj)}"
                elif isinstance(error_obj, dict):
                    error_msg = f"Realtime APIエラー: {error_obj.get('message', 'Unknown error')}"
                else:
                    error_msg = f"Realtime APIエラー: {str(error_obj)}"
            else:
                error_msg = "Realtime APIエラー: Unknown error"

            if self.on_error:
                self.on_error(error_msg)
            print(error_msg)

    def _execute_tool(self, call_id: str, name: str, arguments_str: str) -> None:
        """
        ツールを実行し、結果をRealtime APIに送信

        Args:
            call_id: コールID
            name: 関数名
            arguments_str: 引数（JSON文字列）
        """
        try:
            if not self.tool_handler:
                print("ツールハンドラが設定されていません")
                return

            print(f"ツール実行開始: {name}, args={arguments_str}")

            # 引数をパース
            try:
                arguments = json.loads(arguments_str)
            except json.JSONDecodeError:
                print(f"引数のJSONパースエラー: {arguments_str}")
                arguments = {}

            # ツールを実行
            result = self.tool_handler(name, arguments)
            print(
                f"ツール実行結果: {result[:100]}..."
            )  # 結果が長い場合は省略してログ出力

            # 結果を送信
            if self.session:
                self.session.send(
                    {
                        "type": "conversation.item.create",
                        "item": {
                            "type": "function_call_output",
                            "call_id": call_id,
                            "output": result,
                        },
                    }
                )

                # レスポンス生成をトリガー
                self.session.send({"type": "response.create"})

        except Exception as e:
            error_msg = f"ツール実行エラー: {str(e)}"
            print(error_msg)
            if self.on_error:
                self.on_error(error_msg)

    def send_audio(self, audio_data: bytes) -> bool:
        """
        音声データを送信

        Args:
            audio_data: 音声データ（バイト列）

        Returns:
            送信成功時True、失敗時False
        """
        if not self.is_connected or not self.session:
            return False

        try:
            # base64エンコード
            audio_base64 = base64.b64encode(audio_data).decode("utf-8")

            # イベントを送信
            self.session.send(
                {
                    "type": "input_audio_buffer.append",
                    "audio": audio_base64,
                }
            )

            return True

        except Exception as e:
            error_msg = f"音声データ送信エラー: {str(e)}"
            if self.on_error:
                self.on_error(error_msg)
            print(error_msg)
            return False

    def send_text(self, text: str) -> bool:
        """
        テキストを送信

        Args:
            text: 送信するテキスト

        Returns:
            送信成功時True、失敗時False
        """
        if not self.is_connected or not self.session:
            return False

        try:
            # テキストイベントを送信
            self.session.send(
                {
                    "type": "conversation.item.create",
                    "item": {
                        "type": "message",
                        "role": "user",
                        "content": [
                            {
                                "type": "input_text",
                                "text": text,
                            }
                        ],
                    },
                }
            )

            # 送信完了を通知
            self.session.send(
                {
                    "type": "response.create",
                }
            )

            return True

        except Exception as e:
            error_msg = f"テキスト送信エラー: {str(e)}"
            if self.on_error:
                self.on_error(error_msg)
            print(error_msg)
            return False

    def disconnect(self) -> None:
        """Realtime APIセッションを終了"""
        if self.connection_manager:
            try:
                # コンテキストマネージャーの__exit__を呼び出して接続を終了
                self.connection_manager.__exit__(None, None, None)
            except Exception as e:
                print(f"Realtime API切断エラー: {str(e)}")
            finally:
                self.session = None
                self.connection_manager = None
                self.is_connected = False
