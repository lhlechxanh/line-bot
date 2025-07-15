import os
from flask import Flask, request, abort
from dotenv import load_dotenv
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage
import openai

load_dotenv()

app = Flask(__name__)

line_bot_api = LineBotApi(os.getenv("LINE_CHANNEL_ACCESS_TOKEN"))
handler = WebhookHandler(os.getenv("LINE_CHANNEL_SECRET"))
openai.api_key = os.getenv("OPENAI_API_KEY")

system_prompt = """
你是一位住在台灣的可愛女性朋友，母語是繁體中文，也會一些簡單英文。

你正在和一位正在學繁體中文的外國朋友聊天。請使用繁體中文對話，並在需要時加入拼音與簡單的英文解釋。語氣自然、友善、溫柔，像朋友一樣互動。

聊天風格應該是輕鬆日常的，不要太正式。可以從簡單的問候開始，鼓勵對方多說中文。

當對方說錯，請善意地糾正，舉出正確說法並附拼音。例如：「你可以說：『...』(pinyin) 這樣比較自然喔！」

如果對方聽不懂，用簡單中文或英文簡單解釋意思即可，不要逐字翻譯。

盡量少用 emoji，但偶爾使用一些可愛的表情（例如 🥰☺️）讓對話更有親和力。

目標：幫助對方提升聽說能力與中文語感。
"""

# Đọc danh sách người dùng được phép
with open("allowed_users.txt", "r") as f:
    allowed_users = {line.strip() for line in f.readlines()}


def ask_gpt(user_message):
    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message},
        ],
        temperature=0.7,
    )
    return response.choices[0].message["content"]


@app.route("/callback", methods=["POST"])
def callback():
    signature = request.headers["X-Line-Signature"]
    body = request.get_data(as_text=True)

    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)

    return "OK"


@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    user_id = event.source.user_id

    if user_id not in allowed_users:
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text="對不起，您沒有使用這個機器人的權限喔 🙏")
        )
        return

    user_message = event.message.text
    reply = ask_gpt(user_message)

    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=reply)
    )


if __name__ == "__main__":
    app.run()
