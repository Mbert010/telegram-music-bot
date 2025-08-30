import os
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

API_TOKEN = os.environ.get("API_TOKEN")
CHANNEL_ID = os.environ.get("CHANNEL_ID")
COUNTER_FILE = "counter.txt"

# خواندن شمارنده از فایل
def read_counter():
    if os.path.exists(COUNTER_FILE):
        with open(COUNTER_FILE, "r") as f:
            return int(f.read())
    return 1

# ذخیره شمارنده در فایل
def save_counter(counter):
    with open(COUNTER_FILE, "w") as f:
        f.write(str(counter))

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("سلام! آهنگ هاتو فوروارد کن تا ارسال کنم.")

async def handle_audio(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message
    counter = read_counter()

    # متن کپشن جدید (گزینه 2)
    new_caption = (
        f"✨ آهنگ تازه منتشر شد!\n"
        f"برای تجربه موسیقی‌های بیشتر، حتماً کانال ما رو دنبال کنید: {CHANNEL_ID}\n"
        f"کد آهنگ: {counter}"
    )

    # ارسال آهنگ به کانال
    if msg.audio:
        await context.bot.send_audio(chat_id=CHANNEL_ID, audio=msg.audio.file_id, caption=new_caption)
    elif msg.voice:
        await context.bot.send_voice(chat_id=CHANNEL_ID, voice=msg.voice.file_id, caption=new_caption)
    else:
        await msg.reply_text("فرمت پشتیبانی نمی‌شود!")
        return

    # افزایش شمارنده و ذخیره در فایل
    counter += 1
    save_counter(counter)

    await msg.reply_text("آهنگ با موفقیت ارسال شد!")

# برنامه اصلی
app = ApplicationBuilder().token(API_TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(MessageHandler(filters.AUDIO | filters.VOICE, handle_audio))

app.run_polling()
