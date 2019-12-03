from flask import Flask, request, abort

from linebot import (
   LineBotApi, WebhookHandler
)
from linebot.exceptions import (
   InvalidSignatureError
)
from linebot.models import (
   MessageEvent, TextMessage, TextSendMessage,
)

import os
import hotel

app = Flask(__name__)

YOUR_CHANNEL_ACCESS_TOKEN = os.environ["YOUR_CHANNEL_ACCESS_TOKEN"]
YOUR_CHANNEL_SECRET = os.environ["YOUR_CHANNEL_SECRET"]

line_bot_api = LineBotApi(YOUR_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(YOUR_CHANNEL_SECRET)

@app.route("/")
def hello_world():
   return "hello world!"

@app.route("/callback", methods=['POST'])
def callback():
   # get X-Line-Signature header value
   signature = request.headers['X-Line-Signature']

   # get request body as text
   body = request.get_data(as_text=True)
   app.logger.info("Request body: " + body)

   # handle webhook body
   try:
       handler.handle(body, signature)
   except InvalidSignatureError:
       print("Invalid signature. Please check your channel access token/channel secret.")
       abort(400)

   return 'OK'

@handler.add(MessageEvent, message=TextMessage)
#テキストメッセージを受け取った場合、という意味

#@handler.addから始まる部分はif...elif文のようなイメージで場合分けして書くもので、例えば画像メッセージを受け取った場合の処理を分けたいなら、
#    @handler.add(MessageEvent, message=ImageMessage)
#と、別に書く必要があります。
#テキストも画像もまとめて処理をしたいなら
#    @handler.add(MessageEvent, message=(TextMessage, ImageMessage)
#と書くことができます。
def handle_message(event):
   push_text = event.message.text
   #event.message.textでユーザーから受け取ったメッセージを取得することができます。
   results = hotel.extract_words(push_text)
   if isinstance(results, tuple):
       msg = hotel.hotel_search(*results)
   else:
       msg = results
   line_bot_api.reply_message(event.reply_token,TextSendMessage(text=msg))
 if __name__ == "__main__":
   port = int(os.getenv("PORT"))
   app.run(host="0.0.0.0", port=port)
