"""第1回: 素のLLMに質問するスクリプト。

使い方:
    uv run python -m app.ask "LoRAとは何ですか？"
    uv run python -m app.ask            # 質問を省略すると、講座に固有の質問をする
    uv run python -m app.ask --chat     # 会話履歴を保ったまま続けて質問する（宿題：実装）

ツールを持たない「素の」呼び出し。
講座に固有のことを聞くと、「分からない」と答えるか、一般論でもっともらしく答える
（講座の実際とは違う）ことを確かめよう。
（第3回で、用語集を検索できるエージェントにして改善する）
"""

import argparse

from google import genai
from google.genai import errors

from app.config import MODEL, api_error_message, get_api_key

# 講座に固有の質問。正しい答えは data/glossary.json の homework-levels にある
DEFAULT_QUESTION = "AIE2026の講座の宿題にある「3レベル」とは何ですか？"

EXIT_WORDS = {"exit", "quit", "q", "終了"}


def format_usage(response) -> str:
    """response.usage_metadata から入力・出力トークン数を1行にまとめる。"""
    usage = getattr(response, "usage_metadata", None)
    if usage is None:
        return "[tokens] 取得できませんでした"
    prompt = usage.prompt_token_count or 0
    output = usage.candidates_token_count or 0
    return f"[tokens] 入力: {prompt} / 出力: {output}"


def ask(question: str) -> str:
    client = genai.Client(api_key=get_api_key())
    response = client.models.generate_content(model=MODEL, contents=question)

    # 第1回 演習: 入力トークン数と出力トークン数を表示する
    print(format_usage(response))

    return response.text


def chat_loop(client=None, input_fn=input, first_question: str | None = None) -> None:
    """会話履歴を保ったまま、続けて質問できる対話モード（宿題：実装）。

    client.chats.create で作ったチャットは、送受信したメッセージを履歴として保持し、
    send_message のたびに履歴ごとモデルに送る。そのため前の質問を踏まえて答えられる。
    """
    if client is None:
        client = genai.Client(api_key=get_api_key())
    chat = client.chats.create(model=MODEL)
    print("会話モード（exit / quit / 終了 で終わる。空行は無視）\n")

    question = first_question
    while True:
        if question is None:
            try:
                question = input_fn("あなた> ").strip()
            except (EOFError, KeyboardInterrupt):
                print()
                break
        if not question:
            question = None
            continue
        if question.lower() in EXIT_WORDS:
            break

        try:
            response = chat.send_message(question)
        except errors.APIError as e:
            # レート制限などで失敗しても会話は続けられるようにする
            print(api_error_message(e.code, e.message))
        else:
            print(f"モデル> {response.text}")
            turns = len(chat.get_history()) // 2
            print(f"{format_usage(response)}  [履歴] {turns} 往復\n")
        question = None


def main() -> None:
    parser = argparse.ArgumentParser(description="素のLLMに質問する")
    parser.add_argument("question", nargs="?", default=None)
    parser.add_argument(
        "--chat", action="store_true", help="会話履歴を保ったまま続けて質問する"
    )
    args = parser.parse_args()

    print(f"[model] {MODEL}")
    if args.chat:
        chat_loop(first_question=args.question)
        return

    question = args.question or DEFAULT_QUESTION
    print(f"[質問] {question}\n")
    try:
        print(ask(question))
    except errors.APIError as e:
        print(api_error_message(e.code, e.message))
        raise SystemExit(1)


if __name__ == "__main__":
    main()
