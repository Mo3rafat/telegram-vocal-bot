import asyncio, os, tempfile, subprocess
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters
import logging
import os

# نجيب التوكن من متغير البيئة
TOKEN = os.getenv("TOKEN")
logging.basicConfig(level=logging.INFO)

# ---------- دالة فصل الصوت ----------
async def separate_vocals(input_path: str) -> str:
    out_dir = tempfile.mkdtemp()
    cmd = [
        "python", "-m", "demucs.separate",
        "-n", "htdemucs", "--two-stems", "vocals",
        "-o", out_dir, input_path
    ]
    subprocess.run(cmd, check=True)
    # هنرجع أول ملف vocals ناتج
    for root, dirs, files in os.walk(out_dir):
        for file in files:
            if file == "vocals.wav":
                return os.path.join(root, file)

# ---------- أوامر البوت ----------
async def start(update: Update, context):
    await update.message.reply_text("🎙️ أرسل لي مقطع صوت أو فيديو وسأفصله عن الموسيقى ✂️")

async def handle_audio(update: Update, context):
    msg = await update.message.reply_text("جارٍ المعالجة... استغفر ربك 🌙")
    file = await update.message.effective_attachment.get_file()
    with tempfile.NamedTemporaryFile(suffix=".mp3") as f:
        await file.download_to_drive(f.name)
        try:
            vocals_path = await asyncio.to_thread(separate_vocals, f.name)
            await update.message.reply_audio(open(vocals_path, "rb"))
        except Exception as e:
            logging.error(e)
            await update.message.reply_text("❌ حصل خطأ أثناء الفصل.")
    await msg.delete()

# ---------- تشغيل البوت ----------
def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(
        filters.AUDIO | filters.VOICE | filters.VIDEO | filters.Document.AUDIO,
        handle_audio))
    app.run_polling()

if __name__ == "__main__":
    main()

