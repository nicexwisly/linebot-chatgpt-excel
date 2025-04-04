from flask import Flask, request, abort
import pandas as pd
import openai
import os
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage

app = Flask(__name__)

LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
LINE_CHANNEL_SECRET = os.getenv("LINE_CHANNEL_SECRET")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)
openai.api_key = OPENAI_API_KEY

EXCEL_PATH = "data.xlsx"

@app.route("/callback", methods=['POST'])
def callback():
    signature = request.headers['X-Line-Signature']
    body = request.get_data(as_text=True)

    print("📨 LINE webhook เข้ามาแล้ว")

    try:
        handler.handle(body, signature)
        print("✅ handler.handle สำเร็จ")
    except InvalidSignatureError:
        print("❌ Signature ไม่ถูกต้อง")
        abort(400)

    return 'OK'

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    user_text = event.message.text

    # ✅ ตอบกลับเร็วทันทีเพื่อกัน timeout
    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text="กำลังประมวลผลข้อมูล... โปรดรอสักครู่")
    )

    # ❗ ส่วนนี้คือประมวลผลจริง (อยู่นอก reply)
    try:
        df = pd.read_excel(EXCEL_PATH)
        data_preview = df.head(10).to_string(index=False)

        prompt = f"""ฐานข้อมูล:
{data_preview}

คำถามจากผู้ใช้: {user_text}
ช่วยสรุปข้อมูลหรือให้คำตอบให้เข้าใจง่าย"""

        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=300
        )

        reply = response.choices[0].message['content'].strip()

        # ✅ ส่งข้อความ AI ตามหลังด้วย push_message
        line_bot_api.push_message(
            event.source.user_id,
            TextSendMessage(text=reply)
        )

    except Exception as e:
        line_bot_api.push_message(
            event.source.user_id,
            TextSendMessage(text=f"เกิดข้อผิดพลาด: {str(e)}")
        )

if __name__ == "__main__":
    app.run()
