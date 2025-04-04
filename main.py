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

    print("📨 LINE ส่ง Webhook เข้ามาแล้ว")  # <== บรรทัดนี้ช่วย debug สำคัญมาก

    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        print("❌ ลายเซ็นไม่ถูกต้อง")
        abort(400)

    return 'OK'

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    print("📩 ได้รับข้อความจาก LINE แล้ว")

    user_text = event.message.text
    print("💬 ข้อความที่ผู้ใช้ส่งมา:", user_text)

    try:
        df = pd.read_excel(EXCEL_PATH)
        print("📊 อ่าน Excel สำเร็จ")

        data_preview = df.head(10).to_string(index=False)

        prompt = f"""ฐานข้อมูล:
{data_preview}

คำถามจากผู้ใช้: {user_text}
ช่วยสรุปข้อมูลหรือให้คำตอบให้เข้าใจง่าย"""

        print("🤖 ส่ง prompt ไปหา ChatGPT แล้ว")

        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=300
        )

        reply = response.choices[0].message['content'].strip()
        print("✅ ได้ข้อความตอบกลับจาก AI:", reply)

    except Exception as e:
        reply = f"เกิดข้อผิดพลาด: {str(e)}"
        print("❌ ERROR:", str(e))

    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=reply)
    )

if __name__ == "__main__":
    app.run()
