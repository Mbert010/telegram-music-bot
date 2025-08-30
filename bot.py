import os
import logging
import json
import asyncio
from collections import deque
from telegram import Update
from telegram.ext import Application, MessageHandler, CommandHandler, filters, ContextTypes
from telegram.error import RetryAfter

# -------------------------------
# 🔹 توکن ربات از محیط سرور
# -------------------------------
API_TOKEN = os.environ.get("API_TOKEN")  # 🟢 حتما داخل سرور مقدار بده

# -------------------------------
# 🔹 فایل تنظیمات
# -------------------------------
CONFIG_FILE = "config.json"

if not os.path.exists(CONFIG_FILE):
    default_config = {
        "CHANNEL_ID": "@YourChannelID",
        "DEFAULT_CAPTION": "✨ For more music, follow us!"
    }
    with open(CONFIG_FILE, "w") as f:
        json.dump(default_config, f)

def load_config():
    with open(CONFIG_FILE, "r") as f:
        return json.load(f)

def save_config(config):
    with open(CONFIG_FILE, "w") as f:
        json.dump(config, f)

# -------------------------------
# 🔹 لاگ
# -------------------------------
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# -------------------------------
# 🔹 صف فایل‌ها
# -------------------------------
queue = deque()
is_processing = False

# -------------------------------
# 🔹 شمارنده فایل‌ها (جداگانه)
# -------------------------------
def get_next_number(file_type):
    if file_type == "audio":
        counter_file = "track_counter.txt"
    elif file_type == "video":
        counter_file = "video_counter.txt"
    elif file_type == "document":
        counter_file = "file_counter.txt"
    else:
        counter_file = "counter.txt"

    if not os.path.exists(counter_file):
        with open(counter_file, "w") as f:
            f.write("1")
        return 1

    with open(counter_file, "r") as f:
        num = int(f.read().strip())

    with open(counter_file, "w") as f:
        f.write(str(num + 1))

    return num

# -------------------------------
# 🔹 پردازش صف با تاخیر هوشمند
# -------------------------------
async def process_queue(app: Application):
    global is_processing
    if is_processing or not queue:
        return
    is_processing = True

    config = load_config()
    channel_id = config["CHANNEL_ID"]
    default_caption = config["DEFAULT_CAPTION"]

    while queue:
        update, context, media = queue.popleft()
        file_type, file_obj = media
        number = get_next_number(file_type)

        # تعیین پیشوند بر اساس نوع فایل
        if file_type == "audio":
            prefix = "🎵 Track"
        elif file_type == "video":
            prefix = "📹 Video"
        elif file_type == "document":
            prefix = "📁 File"
        else:
            prefix = "📄 File"

        caption = f"{prefix} #{number}\n\n{default_caption}\n👉 {channel_id}"

        try:
            if file_type == "audio":
                await context.bot.send_audio(chat_id=channel_id,
                                             audio=file_obj.file_id,
                                             caption=caption)
            elif file_type == "document":
                await context.bot.send_document(chat_id=channel_id,
                                                document=file_obj.file_id,
                                                caption=caption)
            elif file_type == "video":
                await context.bot.send_video(chat_id=channel_id,
                                             video=file_obj.file_id,
                                             caption=caption)

            logger.info(f"فایل شماره {number} ارسال شد ✅")
            await update.message.reply_text(f"فایل #{number} به کانال ارسال شد ✅")
            await asyncio.sleep(5)  # ⬅️ تاخیر کوتاه بین فایل‌ها

        except RetryAfter as e:
            wait_time = e.retry_after
            logger.warning(f"Flood Control: صبر {wait_time} ثانیه")
            await asyncio.sleep(wait_time)
            queue.appendleft((update, context, media))

        except Exception as e:
            logger.error(f"خطا در ارسال فایل شماره {number}: {e}")
            await asyncio.sleep(5)

    is_processing = False

# -------------------------------
# 🔹 هندلر دریافت فایل‌ها
# -------------------------------
async def handle_media(update: Update, context: ContextTypes.DEFAULT_TYPE):
    media = None
    if update.message.audio:
        media = ("audio", update.message.audio)
    elif update.message.document:
        media = ("document", update.message.document)
    elif update.message.video:
        media = ("video", update.message.video)
    else:
        await update.message.reply_text("❌ این نوع فایل پشتیبانی نمی‌شود.")
        return

    queue.append((update, context, media))
    logger.info("فایل به صف اضافه شد 🎶")
    await process_queue(context.application)

# -------------------------------
# 🔹 دستورات ادمین
# -------------------------------
ADMIN_ID = 6302319173  # 🔹 آیدی عددی خودت

async def set_channel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("❌ شما دسترسی ادمین ندارید!")
        return
    if not context.args:
        await update.message.reply_text("استفاده: /setchannel @NewChannelID")
        return
    new_channel = context.args[0]
    config = load_config()
    config["CHANNEL_ID"] = new_channel
    save_config(config)
    await update.message.reply_text(f"✅ کانال جدید ذخیره شد: {new_channel}")

async def set_caption(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("❌ شما دسترسی ادمین ندارید!")
        return
    new_caption = " ".join(context.args)
    if not new_caption:
        await update.message.reply_text("استفاده: /setcaption متن جدید")
        return
    config = load_config()
    config["DEFAULT_CAPTION"] = new_caption
    save_config(config)
    await update.message.reply_text(f"✅ کپشن پیش‌فرض به روز شد:\n{new_caption}")

# -------------------------------
# 🔹 اجرای ربات
# -------------------------------
def main():
    app = Application.builder().token(API_TOKEN).build()
    app.add_handler(MessageHandler(filters.AUDIO | filters.Document.ALL | filters.VIDEO, handle_media))
    app.add_handler(CommandHandler("setchannel", set_channel))
    app.add_handler(CommandHandler("setcaption", set_caption))
    print("✅ ربات روشن شد! چند فایل همزمان هم قابل پردازشه 🎶")
    app.run_polling()

if __name__ == "__main__":
    main()
