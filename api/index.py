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

# 🎯 এখানে আপনি যত খুশি গ্রুপ বা চ্যানেল বাটনের নাম ও ইউজারনেম যোগ করতে পারবেন।
# ⚠️ মনে রাখবেন: সব চ্যানেল ও গ্রুপে আপনার বটটিকে অবশ্যই 'Admin' বানাতে হবে।
CHANNELS = [
    {"name": "📢 আমাদের মেইন চ্যানেল", "username": "ffallfileupdate"},
    {"name": "👥 আমাদের ব্যাকআপ গ্রুপ", "username": "এখানে_আপনার_গ্রুপের_ইউজারনেম_দিন"},
    {"name": "🎬 মুভি আপডেট চ্যানেল", "username": "এখানে_আরেকটি_ইউজারনেম_দিন"}
]
# =============================================================

# --- বট এবং ডাটাবেজ কানেকশন ---
bot = telebot.TeleBot(BOT_TOKEN, threaded=False)
mongo_client = MongoClient(MONGO_URI)
db = mongo_client[DB_NAME]
files_col = db["files"]

# --- ইউজার সবগুলো গ্রুপে জয়েন আছে কি না তা চেক করার ফাংশন ---
def check_all_subscriptions(user_id):
    for chan in CHANNELS:
        try:
            member = bot.get_chat_member(f"@{chan['username']}", user_id)
            if member.status not in ['member', 'administrator', 'creator']:
                return False
        except Exception:
            # বট যদি কোনো গ্রুপে এডমিন না থাকে, তবে সেফটির জন্য False ধরবে যাতে এডমিন বুঝতে পারে
            return False
    return True

# --- ওয়েবসাইট লিংক চেক (হোমপেজ) ---
@app.route('/', methods=['GET'])
def home():
    return "<h1>TG Bot was nirob</h1>", 200

# --- টেলিগ্রাম ওয়েব হুক রুট ---
@app.route('/webhook', methods=['POST'])
def webhook():
    if request.headers.get('content-type') == 'application/json':
        json_string = request.get_data().decode('utf-8')
        update = telebot.types.Update.de_json(json_string)
        bot.process_new_updates([update])
        return 'OK', 200
    return 'Invalid Request', 400

# --- /start কমান্ড হ্যান্ডলার ---
@bot.message_handler(commands=['start'])
def start_command(message):
    user_id = message.from_user.id
    text_split = message.text.split()
    param = text_split[1] if len(text_split) > 1 else None

    # ১. ইউজার সব গ্রুপ/চ্যানেলে জয়েন আছে কি না চেক করা
    if not check_all_subscriptions(user_id):
        markup = InlineKeyboardMarkup(row_width=1)
        
        # আপনার লিস্টে থাকা সব গ্রুপ অটোমেটিক বাটন হয়ে যাবে
        for chan in CHANNELS:
            markup.add(InlineKeyboardButton(text=chan['name'], url=f"https://t.me/{chan['username']}"))
        
        # ভেরিফাই বাটন
        back_url = f"https://t.me/{bot.get_me().username}?start={param if param else ''}"
        markup.add(InlineKeyboardButton("🔄 Verify / Try Again", url=back_url))
        
        bot.send_message(
            message.chat.id,
            "⚠️ <b>আপনাকে আমাদের সবকটি গ্রুপ ও চ্যানেলে জয়েন হতে হবে!</b>\n\n"
            "নিচের বাটনগুলোতে ক্লিক করে সবগুলোতে জয়েন হয়ে নিন। তারপর <b>Verify</b> বাটনে চাপুন। জয়েন না করে ভেরিফাই করলে ফাইল পাবেন না।",
            reply_markup=markup,
            parse_mode="HTML"
        )
        return

    # ২. ইউজার সব গ্রুপে জয়েন থাকলে ডাটাবেজ থেকে ফাইল পাঠানো
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

    # ৩. কোনো লিংক ছাড়া সাধারণ স্টার্ট দিলে এই মেসেজ যাবে
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("📢 মেইন চ্যানেল", url=f"https://t.me/{CHANNELS[0]['username']}"))
    
    bot.send_message(
        message.chat.id,
        f"👋 হ্যালো <b>{message.from_user.first_name}</b>!\n\n"
        f"আমি একটি ফাইল শেয়ারিং বট। লিংক তৈরি করতে যেকোনো ফাইল (ভিডিও/ডকুমেন্ট) সরাসরি এখানে আপলোড বা ফরওয়ার্ড করুন।{CREDIT_TEXT}",
        reply_markup=markup,
        parse_mode="HTML"
    )

# --- এডমিন ফাইল আপলোড করলে অটো লিংক জেনারেট করার সেকশন ---
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

    # ফাইল আপলোডের সময় ডেসক্রিপশন/ক্যাপশন থাকলে সেটা অটো সেভ হবে
    caption = message.caption if message.caption else "এখানে আপনার কাঙ্ক্ষিত ফাইল রয়েছে।"
    
    # লিংকের জন্য ইউনিক আইডি তৈরি করা
    db_id = file_id[-20:].replace("_", "").replace("-", "")
    
    # ডাটাবেজে আপডেট বা ইনসার্ট করা
    files_col.update_one(
        {"_id": db_id},
        {"$set": {"file_id": file_id, "file_type": file_type, "caption": caption}},
        upsert=True
    )

    # বটের অটোমেটিক গভীর শেয়ারিং লিংক তৈরি
    share_link = f"https://t.me/{bot.get_me().username}?start={db_id}"

    bot.send_message(
        message.chat.id,
        f"✅ <b>আপনার ফাইলটি ডাটাবেজে সেভ হয়েছে এবং লিংক রেডি!</b>\n\n"
        f"📝 <b>ডেসক্রিপশন:</b> {caption}\n\n"
        f"🔗 <b>আপনার শেয়ারিং লিংক:</b> <code>{share_link}</code>\n\n"
        f"<i>এই লিংকটি শেয়ার করুন। লিংকে ক্লিক করলে ইউজারকে আগে সব গ্রুপে জয়েন হতে বলবে, তারপর ফাইল দেবে।</i>{CREDIT_TEXT}",
        parse_mode="HTML"
    )    markup.add(InlineKeyboardButton("📢 আমাদের চ্যানেল", url=f"https://t.me/{CHANNEL_USERNAME}"))
    
    bot.send_message(
        message.chat.id,
        f"👋 হ্যালো **{message.from_user.first_name}**!\n\nআমি একটি ফ্রি ফাইল ডাউনলোডার বট। আপনি এখানে ফাইল আপলোড করে শেয়ারিং লিংক তৈরি করতে পারবেন।{CREDIT_TEXT}",
        reply_markup=markup,
        parse_mode="Markdown"
    )

@bot.callback_query_handler(func=lambda call: True)
def cb_handler(call):
    if call.data == "upload_info":
        bot.edit_message_text(
            "ℹ️ **ফাইল আপলোড করার নিয়ম:**\n\nসরাসরি বটের ইনবক্সে যেকোনো ফাইল পাঠান। সাথে আপনার পছন্দমতো ক্যাপশন বা ডেসক্রিপশন লিখে দিতে পারেন।",
            call.message.chat.id,
            call.message.message_id,
            parse_mode="Markdown"
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

    caption = message.caption if message.caption else "এখানে আপনার ফাইল রয়েছে।"

    last_file = files_col.find_one(sort=[("_id", -1)])
    next_id = (last_file["_id"] + 1) if last_file else 1
    
    files_col.insert_one({
        "_id": next_id,
        "file_id": file_id,
        "file_type": file_type,
        "caption": caption
    })

    string_id = encode_id(next_id)
    share_link = f"https://t.me/{bot.get_me().username}?start={string_id}"

    bot.send_message(
        message.chat.id,
        f"✅ **আপনার ফাইলটি সফলভাবে সেভ হয়েছে!**\n\n"
        f"📝 **ডেসক্রিপশন:** {caption}\n\n"
        f"🔗 **ডাউনলোড লিংক:** `{share_link}`\n\n"
        f"এই লিংকটি সবার সাথে শেয়ার করতে পারেন।{CREDIT_TEXT}",
        parse_mode="Markdown"
                             )
