import os
import telebot
from flask import Flask, request
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from pymongo import MongoClient

app = Flask(__name__)

# ==================== [ কনফিগারেশন সেকশন ] ====================
BOT_TOKEN = "8801111906:AAFFVl18DgPhwZzVNMMUg5NAAuHLQZC6mxQ"
MONGO_URI = "mongodb+srv://Nirob999:JP6K47Cd8K0TEGgs@cluster0.qsvhw83.mongodb.net/?appName=Cluster0"
DB_NAME = "FreeFileBot"
CREDIT_TEXT = "\n\n<b>Developer: nirob</b>"

CHANNELS = [
    {"name": "📢 আমাদের মেইন চ্যানেল", "username": "ffallfileupdate"}
]
# =============================================================

bot = telebot.TeleBot(BOT_TOKEN, threaded=False)
mongo_client = MongoClient(MONGO_URI)
db = mongo_client[DB_NAME]
files_col = db["files"]

def check_all_subscriptions(user_id):
    for chan in CHANNELS:
        try:
            member = bot.get_chat_member(f"@{chan['username']}", user_id)
            if member.status not in ['member', 'administrator', 'creator']:
                return False
        except Exception:
            return False
    return True

@app.route('/', methods=['GET'])
def home():
    return "<h1>TG Bot was nirob</h1>", 200

# 🛠️ Vercel সিকিউরিটি বাইপাস রুট (যাতে টেলিগ্রামের মেসেজ ব্লক না হয়)
@app.route('/webhook', methods=['POST', 'OPTIONS'])
def webhook():
    # OPTIONS রিকোয়েস্ট আসলে Vercel-কে হ্যান্ডশেক সিগন্যাল পাঠানো
    if request.method == 'OPTIONS':
        response = app.make_response(('OK', 200))
        response.headers['Access-Control-Allow-Origin'] = '*'
        response.headers['Access-Control-Allow-Methods'] = 'POST, GET, OPTIONS'
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type'
        return response

    if request.headers.get('content-type') == 'application/json':
        json_string = request.get_data().decode('utf-8')
        update = telebot.types.Update.de_json(json_string)
        bot.process_new_updates([update])
        
        # রেসপন্স হেডারে সিকিউরিটি পারমিশন পাস করা
        response = app.make_response(('OK', 200))
        response.headers['Access-Control-Allow-Origin'] = '*'
        return response
        
    return 'Invalid Request', 400

@bot.message_handler(commands=['start'])
def start_command(message):
    user_id = message.from_user.id
    text_split = message.text.split()
    param = text_split[1] if len(text_split) > 1 else None

    if not check_all_subscriptions(user_id):
        markup = InlineKeyboardMarkup(row_width=1)
        for chan in CHANNELS:
            markup.add(InlineKeyboardButton(text=chan['name'], url=f"https://t.me/{chan['username']}"))
        
        back_url = f"https://t.me/{bot.get_me().username}?start={param if param else ''}"
        markup.add(InlineKeyboardButton("🔄 Verify / Try Again", url=back_url))
        
        bot.send_message(
            message.chat.id,
            "⚠️ <b>আপনাকে আমাদের আপডেট চ্যানেলে জয়েন হতে হবে!</b>\n\n"
            "নিচের বাটনে ক্লিক করে চ্যানেলে জয়েন হয়ে নিন। তারপর <b>Verify / Try Again</b> বাটনে চাপুন। জয়েন না করে ভেরিফাই করলে ফাইল পাবেন না।",
            reply_markup=markup,
            parse_mode="HTML"
        )
        return

    if param:
        try:
            file_data = files_col.find_one({"_id": param})
            if file_data:
                caption = file_data.get("caption", "") + CREDIT_TEXT
                file_type = file_data.get("file_type")
                file_id = file_data["file_id"]

                if file_type == "document":
                    bot.send_document(message.chat.id, file_id, caption=caption, parse_mode="HTML")
                elif file_type == "video":
                    bot.send_video(message.chat.id, file_id, caption=caption, parse_mode="HTML")
                elif file_type == "audio":
                    bot.send_audio(message.chat.id, file_id, caption=caption, parse_mode="HTML")
                elif file_type == "photo":
                    bot.send_photo(message.chat.id, file_id, caption=caption, parse_mode="HTML")
            else:
                bot.send_message(message.chat.id, "❌ ফাইলটি ডাটাবেজে খুঁজে পাওয়া যায়নি বা ডিলিট করা হয়েছে।")
        except Exception:
            bot.send_message(message.chat.id, "❌ কোনো একটি কারিগরি সমস্যা হয়েছে। দয়া করে মূল লিংক থেকে আবার চেষ্টা করুন।")
        return

    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("📢 মেইন চ্যানেল", url=f"https://t.me/{CHANNELS[0]['username']}"))
    
    bot.send_message(
        message.chat.id,
        f"👋 হ্যালো <b>{message.from_user.first_name}</b>!\n\n"
        f"আমি একটি ফাইল শেয়ারিং বট। লিংক তৈরি করতে যেকোনো ফাইল (ভিডিও/ডকুমেন্ট) সরাসরি এখানে আপলোড বা ফরওয়ার্ড করুন।{CREDIT_TEXT}",
        reply_markup=markup,
        parse_mode="HTML"
    )

@bot.message_handler(content_types=['document', 'video', 'audio', 'photo'])
def handle_files(message):
    file_id = None
    file_type = None
    
    if message.document:
        file_id = message.document.file_id
        file_type = "document"
    elif message.video:
        file_id = message.video.file_id
        file_type = "video"
    elif message.audio:
        file_id = message.audio.file_id
        file_type = "audio"
    elif message.photo:
        file_id = message.photo[-1].file_id
        file_type = "photo"

    caption = message.caption if message.caption else "এখানে আপনার কাঙ্ক্ষিত ফাইল রয়েছে।"
    db_id = file_id[-20:].replace("_", "").replace("-", "")
    
    files_col.update_one(
        {"_id": db_id},
        {"$set": {"file_id": file_id, "file_type": file_type, "caption": caption}},
        upsert=True
    )

    share_link = f"https://t.me/{bot.get_me().username}?start={db_id}"

    bot.send_message(
        message.chat.id,
        f"✅ <b>আপনার ফাইলটি ডাটাবেজে সেভ হয়েছে এবং লিংক রেডি!</b>\n\n"
        f"📝 <b>ডেসক্রিপশন:</b> {caption}\n\n"
        f"🔗 <b>আপনার শেয়ারিং লিংক:</b> <code>{share_link}</code>\n\n"
        f"<i>এই লিংকটি শেয়ার করুন। লিংকে ক্লিক করলে ইউজারকে আগে চ্যানেলে জয়েন হতে বলবে, তারপর ফাইল দেবে।</i>{CREDIT_TEXT}",
        parse_mode="HTML"
    )
