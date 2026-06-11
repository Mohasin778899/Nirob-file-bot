import base64
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, Message
from pyrogram.errors import UserNotParticipant
from pymongo import MongoClient

# --- আপনার দেওয়া কনফিগারেশন ---
API_ID = 30215456
API_HASH = "3f21de1981591d8a9b835a2df078c00b"
BOT_TOKEN = "8801111906:AAFFVl18DgPhwZzVNMMUg5NAAuHLQZC6mxQ"
MONGO_URI = "mongodb+srv://Nirob999:JP6K47Cd8K0TEGgs@cluster0.qsvhw83.mongodb.net/?appName=Cluster0"
DB_NAME = "FreeFileBot"

CHANNEL_USERNAME = "ffallfileupdate" 
CREDIT_TEXT = "\n\n**Developer: nirob**"

# --- ডাটাবেজ সেটআপ ---
mongo_client = MongoClient(MONGO_URI)
db = mongo_client[DB_NAME]
files_col = db["files"]

# 💡 Vercel-এর জন্য সেশন ফাইল তৈরি বন্ধ করতে in_memory=True করা হয়েছে
bot = Client(
    "FreeFileBot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN,
    in_memory=True,
    workers=0
)

# --- সাহায্যকারী ফাংশন ---
def encode_id(file_id):
    return base64.urlsafe_b64encode(str(file_id).encode('ascii')).decode('ascii').replace("=", "")

def decode_id(base64_id):
    padding = '=' * (4 - len(base64_id) % 4)
    return int(base64.urlsafe_b64decode((base64_id + padding).encode('ascii')).decode('ascii'))

async def is_subscribed(client, user_id):
    try:
        await client.get_chat_member(CHANNEL_USERNAME, user_id)
        return True
    except UserNotParticipant:
        return False
    except Exception:
        return True 

# --- বটের কমান্ডসমূহ ---
@bot.on_message(filters.command("start") & filters.private)
async def start_command(client, message: Message):
    user_id = message.from_user.id
    param = message.text.split()[1] if len(message.text.split()) > 1 else None
    
    if not await is_subscribed(client, user_id):
        buttons = [
            [InlineKeyboardButton("📢 Join Channel", url=f"https://t.me/{CHANNEL_USERNAME}")],
            [InlineKeyboardButton("🔄 Verify / Try Again", url=f"https://t.me/{client.me.username}?start={param if param else ''}")]
        ]
        await message.reply_text(
            "⚠️ **আপনাকে প্রথমে আমাদের আপডেট চ্যানেলে জয়েন হতে হবে!**\n\nনিচের বাটনে ক্লিক করে জয়েন হয়ে 'Verify' বা 'Try Again' বাটনে চাপুন।",
            reply_markup=InlineKeyboardMarkup(buttons)
        )
        return

    if param:
        try:
            db_id = decode_id(param)
            file_data = files_col.find_one({"_id": db_id})
            
            if file_data:
                caption = file_data.get("caption", "") + CREDIT_TEXT
                await client.send_cached_media(
                    chat_id=user_id,
                    file_id=file_data["file_id"],
                    caption=caption
                )
            else:
                await message.reply_text("❌ ফাইলটি খুঁজে পাওয়া যায়নি।")
        except Exception:
            await message.reply_text("❌ কোনো একটি সমস্যা হয়েছে। আবার চেষ্টা করুন।")
        return

    buttons = [
        [InlineKeyboardButton("📤 ফাইল আপলোড করুন", callback_data="upload_info")],
        [InlineKeyboardButton("📢 আমাদের চ্যানেল", url=f"https://t.me/{CHANNEL_USERNAME}")]
    ]
    await message.reply_text(
        f"👋 হ্যালো **{message.from_user.first_name}**!\n\nআমি একটি ফ্রি ফাইল ডাউনলোডার বট। আপনি এখানে ফাইল আপলোড করে শেয়ারিং লিংক তৈরি করতে পারবেন।{CREDIT_TEXT}",
        reply_markup=InlineKeyboardMarkup(buttons)
    )

@bot.on_callback_query()
async def cb_handler(client, query):
    if query.data == "upload_info":
        await query.message.edit_text(
            "ℹ️ **ফাইল আপলোড করার নিয়ম:**\n\nসরাসরি বটের ইনবক্সে যেকোনো ফাইল পাঠান। সাথে আপনার পছন্দমতো ক্যাপশন বা ডেসক্রিপশন লিখে দিতে পারেন।"
        )

@bot.on_message((filters.document | filters.video | filters.audio | filters.photo) & filters.private)
async def handle_files(client, message: Message):
    media = message.document or message.video or message.audio or message.photo
    file_id = media.file_id if not isinstance(media, list) else media[0].file_id
    caption = message.caption if message.caption else "এখানে আপনার ফাইল রয়েছে।"

    last_file = files_col.find_one(sort=[("_id", -1)])
    next_id = (last_file["_id"] + 1) if last_file else 1
    
    files_col.insert_one({
        "_id": next_id,
        "file_id": file_id,
        "caption": caption
    })

    string_id = encode_id(next_id)
    share_link = f"https://t.me/{client.me.username}?start={string_id}"

    await message.reply_text(
        f"✅ **আপনার ফাইলটি সফলভাবে সেভ হয়েছে!**\n\n"
        f"📝 **ডেসক্রিপশন:** {caption}\n\n"
        f"🔗 **ডাউনলোড লিংক:** `{share_link}`\n\n"
        f"এই লিংকটি সবার সাথে শেয়ার করতে পারেন।{CREDIT_TEXT}",
        disable_web_page_preview=True
)
