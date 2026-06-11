import asyncio
from flask import Flask, request
from pyrogram.types import Update
from bot import bot

app = Flask(__name__)

# সেশন স্টার্ট করা
loop = asyncio.get_event_loop()
if not bot.is_connected:
    loop.run_until_complete(bot.start())

@app.route('/', methods=['GET'])
def home():
    return "Bot is running perfectly on Vercel!"

@app.route('/webhook', methods=['POST'])
def webhook():
    if request.headers.get('content-type') == 'application/json':
        json_string = request.get_data().decode('utf-8')
        update = Update.de_json(bot, json_string)
        loop.run_until_complete(bot.push_update(update))
        return 'OK', 200
    return 'Invalid Request', 400
