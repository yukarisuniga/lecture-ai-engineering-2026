"""app/ask.py の会話モードのテスト（APIキー不要。偽のクライアントを使う）。"""

from types import SimpleNamespace

from app import ask


class FakeChat:
    def __init__(self):
        self.history = []

    def send_message(self, message):
        # 受け取った時点の履歴の長さを答えに含め、履歴が保たれていることを確かめる
        reply = f"reply{len(self.history) // 2 + 1}:{message}"
        self.history += [message, reply]
        usage = SimpleNamespace(prompt_token_count=10, candidates_token_count=5)
        return SimpleNamespace(text=reply, usage_metadata=usage)

    def get_history(self):
        return self.history


class FakeClient:
    def __init__(self):
        self.chat = FakeChat()
        self.chats = SimpleNamespace(create=lambda model: self.chat)


def test_chat_keeps_history(capsys):
    client = FakeClient()
    inputs = iter(["私の名前はユカリです", "", "私の名前は？", "exit"])
    ask.chat_loop(client=client, input_fn=lambda _: next(inputs))

    out = capsys.readouterr().out
    assert "reply1:私の名前はユカリです" in out
    assert "reply2:私の名前は？" in out
    assert "[履歴] 2 往復" in out
    assert client.chat.get_history()[0] == "私の名前はユカリです"


def test_format_usage():
    usage = SimpleNamespace(prompt_token_count=12, candidates_token_count=34)
    assert ask.format_usage(SimpleNamespace(usage_metadata=usage)) == "[tokens] 入力: 12 / 出力: 34"
    assert "取得できません" in ask.format_usage(SimpleNamespace(usage_metadata=None))
