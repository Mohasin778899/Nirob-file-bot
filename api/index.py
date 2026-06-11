import asyncio
from flask import Flask, request
from pyrogram.types import Update
from bot import bot

app = Flask(__name__)

# নতুন ইভেন্ট লুপ তৈরি ও হ্যান্ডেল করা
try:
    loop = asyncio.get_running_loop()
except RuntimeError:
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

# Vercel স্টার্ট হওয়ার সাথে সাথে ক্লায়েন্ট কানেক্ট করা
if not bot.is_connected:
    loop.run_until_complete(bot.connect())

@app.route('/', methods=['GET'])
def home():
    # 🎯 আপনার কাঙ্ক্ষিত লেখাটি এখানে দিয়ে দেওয়া হলো
    return "<h1>TG Bot was nirob</h1>", 200

@app.route('/webhook', methods=['POST'])
def webhook():
    if request.headers.get('content-type') == 'application/json':
        json_string = request.get_data().decode('utf-8')
        update = Update.de_json(bot, json_string)
        
        # ওয়েব হুকের মাধ্যমে মেসেজ প্রসেস করা
        loop.run_until_complete(bot.push_update(update))
        return 'OK', 200
    return 'Invalid Request', 400
