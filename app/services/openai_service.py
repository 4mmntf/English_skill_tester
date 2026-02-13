"""
OpenAI APIサービス
"""

import os
from openai import OpenAI
from typing import Dict, Any


class OpenAIService:
    """OpenAI APIを使用するサービスクラス"""

    def __init__(self) -> None:
        """
        初期化処理
        環境変数からAPIキーを取得し、OpenAIクライアントを初期化する
        """
        # OPENAI_API_KEYまたはOPENAI_APIのどちらかをサポート
        api_key: str | None = os.getenv("OPENAI_API_KEY") or os.getenv("OPENAI_API")
        if not api_key:
            raise ValueError(
                "OPENAI_API_KEYまたはOPENAI_API環境変数が設定されていません"
            )
        self.client: OpenAI = OpenAI(api_key=api_key)
        # 開発中はGPT-5 nano/miniを使用
        self.model: str = os.getenv("OPENAI_MODEL", "gpt-5-nano")

    async def get_realtime_response(self, audio_data: bytes) -> str | None:
        """
        Realtime APIを使用して音声データから応答を取得

        Args:
            audio_data: 音声データ（バイト列）

        Returns:
            AIからの応答テキスト、失敗時はNone
        """
        # TODO: Realtime APIの実装
        pass

    async def evaluate_conversation(self, conversation_text: str) -> Dict[str, Any]:
        """
        GPT-5を使用して会話内容を評価

        Args:
            conversation_text: 評価する会話テキスト（AIと学生の会話を交互に記録した形式）

        Returns:
            評価結果を含む辞書
        """
        prompt: str = f"""
        あなたは厳格な英語会話評価官です。以下の英会話ログを評価してください。

        【重要：ハルシネーション（幻覚）と無音の検出について】
        音声認識システムは、無音時やノイズに対して以下のようなテキストを誤って生成することが頻繁にあります：
        - "Thank you for watching"
        - "Subtitles by..."
        - "MBC News"
        - "Bye."
        - "Okay."
        - その他、文脈と無関係な単発のフレーズ

        **評価ルール（最優先）：**
        1. ユーザー（学生）の発言が上記のフレーズ**のみ**の場合、または実質的な意味のある発言がほぼ皆無（2ターン未満の有意義な会話）の場合は、**全てのスコアを 0 に設定し、is_valid を false にしてください**。
        2. ユーザーが "Yes", "No", "Hello" などの単語しか発していない場合、スコアは **30点以下** に抑えてください。
        3. 70点以上の高得点は、完全な文章で話し、複数回の往復（キャッチボール）が成立している場合のみ与えてください。
        4. 会話が成立していない、またはハルシネーションが多い場合は、全体スコアを大幅に減点してください。
        5. お世辞のような評価は避け、厳格に評価してください。

        【評価基準の追加・変更】
        以下の要素を厳密に評価スコアに反映させてください：

        **加点対象 (+):**
        - **フィラーの適切な使用:** 次に話す内容のトーンを予告するようなフィラー（例: "Well...", "Actually...", "You know..."）を使用している場合。
        - **具体的な語彙:** 文脈に合った、あいまいでない具体的な単語を使用している場合。
        - **言い換え（Circumlocution）:** 単語を忘れた際などに、会話を止めずに別の言葉で説明して繋いでいる場合。

        **減点対象 (-):**
        - **長い沈黙・無音:** 会話のリズムが悪い場合。
        - **母国語の癖:** "Uh..." (日本語的な発音), "Eeto...", "Ano..." など、母国語（日本語）のフィラーが出てしまっている場合。
        - **短文の連続:** 一文が極端に短い発言が続き、会話が深まらない場合。

        【評価観点】
        実質的な会話が行われている場合のみ、以下を評価してください：
        1. 会話レベル (1-10段階): ユーザーの英語レベルを10段階で評価
        2. 文法の正確性 (0-100)
        3. 語彙の適切性 (0-100)
        4. 会話の自然さ (0-100)
        5. 会話の流暢さ (0-100)
        
        また、会話中に出てくる学習者にとって難しいと思われる単語や、重要な単語があれば抽出して解説してください。
        
        会話内容：
        {conversation_text}
        
        評価結果を以下のJSON形式で返してください：
        {{
            "is_valid": true/false,  // 会話として成立しているか（ハルシネーションのみの場合はfalse）
            "conversation_level": 1-10, // 会話レベル（1:初学者 - 10:ネイティブ級）
            "grammar_score": 0-100,  // 文法の正確性スコア
            "vocabulary_score": 0-100,  // 語彙の適切性スコア
            "naturalness_score": 0-100,  // 会話の自然さスコア
            "fluency_score": 0-100,  // 会話の流暢さスコア
            "overall_score": 0-100,  // 総合スコア（ハルシネーションのみなら0）
            "feedback": "評価コメント（無音の場合はその旨を記載）。レベル評価の理由も含めて記述してください。",
            "vocabulary_info": [
                {{
                    "word": "単語",
                    "definition": "定義（日本語）",
                    "example": "例文"
                }}
            ]
        }}
        """

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are an English conversation evaluation expert. Always respond in valid JSON format.",
                    },
                    {"role": "user", "content": prompt},
                ],
                response_format={"type": "json_object"},  # JSON形式で返すことを強制
            )
            content: str | None = response.choices[0].message.content
            if content:
                import json

                try:
                    evaluation_data = json.loads(content)

                    # レベル情報をフィードバックに追加（既存のスキーマを変更しないため）
                    level = evaluation_data.get("conversation_level", 0)
                    original_feedback = evaluation_data.get("feedback", "")
                    enhanced_feedback = (
                        f"**推定会話レベル: {level}/10**\n\n{original_feedback}"
                    )

                    return {
                        "evaluation": enhanced_feedback,
                        "is_valid": evaluation_data.get("is_valid", False),
                        "grammar_score": evaluation_data.get("grammar_score", 0),
                        "vocabulary_score": evaluation_data.get("vocabulary_score", 0),
                        "naturalness_score": evaluation_data.get(
                            "naturalness_score", 0
                        ),
                        "fluency_score": evaluation_data.get("fluency_score", 0),
                        "overall_score": evaluation_data.get("overall_score", 0),
                        "vocabulary_info": evaluation_data.get("vocabulary_info", []),
                    }
                except json.JSONDecodeError:
                    return {
                        "evaluation": content,
                        "is_valid": False,
                        "error": "JSON解析エラー",
                    }
            return {"evaluation": "", "is_valid": False, "error": "レスポンスが空"}
        except Exception as e:
            return {"error": str(e), "is_valid": False}

    async def create_listening_question(self) -> str:
        """
        TOEIC Part 4形式のリスニング問題を生成

        Returns:
            生成された問題テキスト(JSON形式)
        """
        prompt = """TOEICのPart 4: ロングセリフ（説明文）セクションのような英文と、それぞれの英文に対して2つの問題を生成してください。これを5セット（合計5つの英文と10問）生成してください。
        生成された英文が被らないように多様なトピックを選び、"Welcome to ..."のような定型文は避けてください。

        【重要：難易度設定】
        各英文に対する2つの問題について、以下の難易度設定を厳守してください：
        1問目：【低難易度 (Easy / CEFR A2-B1レベル)】
          - テキスト内で明示的に述べられている事実やキーワードを聞き取るだけの単純な問題にしてください。
          - 選択肢も単純で分かりやすいものにしてください。
        2問目：【高難易度 (Hard / CEFR C1レベル)】
          - 推論が必要な問題、言い換え（パラフレーズ）が多用されている問題、または文脈全体の理解が必要な問題にしてください。
          - 語彙レベルを高くし、ひっかけの選択肢を含めてください。

        【重要：長さの制限】
        各英文の長さは、**80〜120単語程度**（読み上げ時間30〜45秒相当）にしてください。長すぎると受験者の負担になるため、適切な長さを厳守してください。

        【重要：正解の分散】
        正解の選択肢（A, B, C, D）は偏りがないようにランダムに分散させてください。すべての問題の答えが同じになったり、Bに偏ったりしないように、A, B, C, Dをバランスよく配置してください。
        
        以下のJSON形式で出力してください:
        {
            "passages": [
                {
                    "passage": "English passage text 1...",
                    "problems": [
                        {
                            "question": "Question 1 (Easy)...",
                            "options": ["Option A", "Option B", "Option C", "Option D"],
                            "answer": "A" (A, B, C, or D)
                        },
                        {
                            "question": "Question 2 (Hard)...",
                            "options": ["Option A", "Option B", "Option C", "Option D"],
                            "answer": "B" (A, B, C, or D)
                        }
                    ]
                },
                ... (repeat for 5 passages)
            ]
        }
        """

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a helpful assistant that generates English listening tests in JSON format.",
                    },
                    {"role": "user", "content": prompt},
                ],
                response_format={"type": "json_object"},
            )
            return response.choices[0].message.content or ""
        except Exception as e:
            print(f"問題生成エラー: {e}")
            return ""

    async def create_grammar_question(self) -> str:
        """
        TOEIC Part 5/6形式の文法問題を生成

        Returns:
            生成された問題テキスト(JSON形式)
        """
        prompt = """TOEIC Part 5（短文穴埋め問題）形式の文法問題を5問生成してください。
        文法知識（時制、品詞、関係詞、前置詞など）や語彙力を問う問題を作成してください。

        【重要：難易度設定】
        5問の中で難易度を分散させてください：
        - 1-2問：【低難易度 (Basic)】基本的な文法事項（三単現のs、基本時制など）
        - 2-3問：【中難易度 (Intermediate)】TOEIC 600点レベル（受動態、現在完了、接続詞など）
        - 1-2問：【高難易度 (Advanced)】TOEIC 800点以上レベル（仮定法、倒置、難解な語彙など）

        以下のJSON形式で出力してください:
        {
            "questions": [
                {
                    "question": "The manager _______ the report yesterday.",
                    "options": ["writes", "wrote", "written", "writing"],
                    "answer": "B" (A, B, C, or D),
                    "explanation": "Yesterday（昨日）という過去を表す副詞があるため、過去形のwroteが正解です。"
                },
                ... (repeat for 5 questions)
            ]
        }
        """

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a helpful assistant that generates English grammar tests in JSON format.",
                    },
                    {"role": "user", "content": prompt},
                ],
                response_format={"type": "json_object"},
            )
            return response.choices[0].message.content or ""
        except Exception as e:
            print(f"文法問題生成エラー: {e}")
            return ""

    async def generate_speech(self, text: str, output_path: str) -> bool:
        """
        テキストから音声を生成して保存

        Args:
            text: 音声化するテキスト
            output_path: 保存先のパス

        Returns:
            成功したかどうか
        """
        print(text)
        try:
            response = self.client.audio.speech.create(
                model="tts-1",
                voice="alloy",
                input=text,
            )
            response.stream_to_file(output_path)
            return True
        except Exception as e:
            print(f"音声生成エラー: {e}")
            return False

    async def predict_total_score(
        self,
        conversation_text: str,
        listening_results: list[Dict[str, Any]],
        grammar_results: list[Dict[str, Any]] | None = None,
    ) -> Dict[str, Any]:
        """
        会話とリスニングと文法テストの結果からTOEICスコアを予測

        Args:
            conversation_text: 会話の書き起こしテキスト
            listening_results: リスニングテストの結果リスト
            grammar_results: 文法テストの結果リスト（オプション）
                [{
                    "question": str,
                    "options": list[str],
                    "correct_answer": str,
                    "user_answer": str,
                    "is_correct": bool
                }, ...]

        Returns:
            予測結果を含む辞書
            {
                "predicted_score": int,
                "listening_score": int,
                "reading_score": int,
                "reasoning": str
            }
        """
        prompt = f"""
        あなたは英語のエキスパートです。
        以下の「英会話テストの会話ログ」、「リスニングテストの回答結果」、および「文法テストの回答結果」に基づいて、この受験者の総合スコアを予測してください。

        【予測の根拠】
        - 会話ログから、文法力、語彙力、流暢さ、応答の適切さを分析し、Reading/Speaking能力の代替指標として考慮してください。
        - リスニング回答結果から、聴解力を分析してください。
        
        【リスニングテストの難易度設定】
        リスニングテストは、各パッセージにつき2問出題されています。
        - 1問目：【低難易度 (Easy / CEFR A2-B1)】単純な聞き取り
        - 2問目：【高難易度 (Hard / CEFR C1)】推論や高度な理解が必要
        
        【文法テストの難易度設定】
        文法テストは合計5問出題されています。
        - 1-2問：【低難易度 (Basic)】基本的な文法事項
        - 2-3問：【中難易度 (Intermediate)】TOEIC 600点レベル
        - 1-2問：【高難易度 (Advanced)】TOEIC 800点以上レベル

        回答結果を分析する際は、この難易度設定を考慮してください。高難易度の問題に正解している場合は、特に高く評価してください。

        【データ】
        === 会話ログ ===
        {conversation_text}

        === リスニングテスト結果 ===
        {str(listening_results)}

        === 文法テスト結果 ===
        {str(grammar_results) if grammar_results else "（未実施）"}

        【出力フォーマット】
        以下のJSON形式で出力してください。
        {{
            "predicted_score": 10-1000, // 合計予測スコア (5点刻み)
            "listening_score": 5-500,  // リスニングセクション予測スコア
            "reading_score": 5-500,    // リーディングセクション予測スコア (会話力と文法テストから推測)
            "reasoning": "スコアの根拠となる詳細な分析コメント（日本語で記述）。リスニング、リーディング（文法含む）それぞれの強み・弱みに言及してください。"
        }}
        """

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a TOEIC score prediction expert. Always respond in valid JSON format.",
                    },
                    {"role": "user", "content": prompt},
                ],
                response_format={"type": "json_object"},
            )
            content = response.choices[0].message.content
            if content:
                import json

                try:
                    result = json.loads(content)
                    return {
                        "predicted_score": result.get("predicted_score", 0),
                        "listening_score": result.get("listening_score", 0),
                        "reading_score": result.get("reading_score", 0),
                        "reasoning": result.get("reasoning", ""),
                    }
                except json.JSONDecodeError:
                    return {"error": "JSON解析エラー", "predicted_score": 0}
            return {"error": "レスポンスが空", "predicted_score": 0}
        except Exception as e:
            return {"error": str(e), "predicted_score": 0}
