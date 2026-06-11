import os
import base64
from flask import Flask, request
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from pymongo import MongoClient

app = Flask(__name__)

# --- কনফিগারেশন ---
BOT_TOKEN = "8801111906:AAFFVl18DgPhwZzVNMMUg5NAAuHLQZC6mxQ"
MONGO_URI = "mongodb+srv://Nirob999:JP6K47Cd8K0TEGgs@cluster0.qsvhw83.mongodb.net/?appName=Cluster0"
DB_NAME = "FreeFileBot"
CHANNEL_USERNAME = "ffallfileupdate"
CREDIT_TEXT = "\n\n**Developer: nirob**"

# --- বট এবং ডাটাবেজ ইনিশিয়ালাইজ ---
bot = telebot.TeleBot(BOT_TOKEN, threaded=False)
mongo_client = MongoClient(MONGO_URI)
db = mongo_client[DB_NAME]
files_col = db["files"]

# --- সাহায্যকারী ফাংশন ---
def encode_id(file_id):
    return base64.urlsafe_b64encode(str(file_id).encode('ascii')).decode('ascii').replace("=", "")

def decode_id(base64_id):
    padding = '=' * (4 - len(base64_id) % 4)
    return int(base64.urlsafe_b64decode((base64_id + padding).encode('ascii')).decode('ascii'))

def is_subscribed(user_id):
    try:
        member = bot.get_chat_member(f"@{CHANNEL_USERNAME}", user_id)
        if member.status in ['member', 'administrator', 'creator']:
            return True
        return False
    except Exception:
        return True

# --- ওয়েবসাইট লিংক চেক ---
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

# --- বটের কমান্ডসমূহ ---
@bot.message_handler(commands=['start'])
def start_command(message):
    user_id = message.from_user.id
    text_split = message.text.split()
    param = text_split[1] if len(text_split) > 1 else None

    if not is_subscribed(user_id):
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("📢 Join Channel", url=f"https://t.me/{CHANNEL_USERNAME}"))
        markup.add(InlineKeyboardButton("🔄 Verify / Try Again", url=f"https://t.me/{bot.get_me().username}?start={param if param else ''}"))
        
        bot.send_message(
            message.chat.id,
            "⚠️ **আপনাকে প্রথমে আমাদের আপডেট চ্যানেলে জয়েন হতে হবে!**\n\nনিচের বাটনে ক্লিক করে জয়েন হয়ে 'Verify' বা 'Try Again' বাটনে চাপুন।",
            reply_markup=markup,
            parse_mode="Markdown"
        )
        return

    if param:
        try:
            db_id = decode_id(param)
            file_data = files_col.find_one({"_id": db_id})
            
            if file_data:
                caption = file_data.get("caption", "") + CREDIT_TEXT
                file_type = file_data.get("file_type")
                file_id = file_data["file_id"]

                if file_type == "document":
                    bot.send_document(message.chat.id, file_id, caption=caption, parse_mode="Markdown")
                elif file_type == "video":
                    bot.send_video(message.chat.id, file_id, caption=caption, parse_mode="Markdown")
                elif file_type == "audio":
                    bot.send_audio(message.chat.id, file_id, caption=caption, parse_mode="Markdown")
                elif file_type == "photo":
                    bot.send_photo(message.chat.id, file_id, caption=caption, parse_mode="Markdown")
            else:
                bot.send_message(message.chat.id, "❌ ফাইলটি খুঁজে পাওয়া যায়নি।")
        except Exception:
            bot.send_message(message.chat.id, "❌ কোনো একটি সমস্যা হয়েছে। আবার চেষ্টা করুন।")
        return

    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("📤 ফাইল আপলোড করুন", callback_data="upload_info"))
    markup.add(InlineKeyboardButton("📢 আমাদের চ্যানেল", url=f"https://t.me/{CHANNEL_USERNAME}"))
    
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
