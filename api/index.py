import asyncio
from flask import Flask, request
from pyrogram.types import Update
from bot import bot

app = Flask(__name__)

# নতুন থ্রেড বা রিকোয়েস্টের জন্য লুপ ম্যানেজমেন্ট
try:
    loop = asyncio.get_running_loop()
except RuntimeError:
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

if not bot.is_connected:
    loop.run_until_complete(bot.start())

@app.route('/', methods=['GET'])
def home():
    # লিংকে ঢুকলে এখন এই লেখাটি শো করবে
    return "<h1>TG Bot was nirob</h1>", 200

@app.route('/webhook', methods=['POST'])
def webhook():
    if request.headers.get('content-type') == 'application/json':
        json_string = request.get_data().decode('utf-8')
        update = Update.de_json(bot, json_string)
        
        # ক্র্যাশ আটকাতে সেফলি রান করা হচ্ছে
        local_loop = asyncio.new_event_loop()
        local_loop.run_until_complete(bot.push_update(update))
        local_loop.close()
        
        return 'OK', 200
    return 'Invalid Request', 400
