import asyncio, os, tempfile, subprocess, logging
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters
import yt_dlp

TOKEN = os.getenv("TOKEN")
logging.basicConfig(level=logging.INFO)

async def download_audio_from_url(url: str) -> str:
    tmpdir = tempfile.mkdtemp()
    output_path = os.path.join(tmpdir, "audio.%(ext)s")
    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': output_path,
        'quiet': True,
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        filename = ydl.prepare_filename(info)
        return os.path.join(tmpdir, f"audio.mp3")

async def separate_vocals(input_path: str) -> str:
    out_dir = tempfile.mkdtemp()
    cmd = [
        "python", "-m", "demucs.separate",
        "-n", "htdemucs", "--two-stems", "vocals",
        "-o", out_dir, input_path
    ]
    subprocess.run(cmd, check=True)
    for root, dirs, files in os.walk(out_dir):
        for file in files:
            if file == "vocals.wav":
                return os.path.join(root, file)

async def start(update: Update, context):
    await update.message.reply_text("🎙️ أرسل رابط لفيديو أو مقطع وسأفصل الصوت عن الموسيقى.")

async def handle_message(update: Update, context):
    text = update.message.text
    if text and text.startswith("http"):
        msg = await update.message.reply_text("📥 جارٍ تحميل الفيديو ومعالجته... ⏳")
        try:
            audio_path = await asyncio.to_thread(download_audio_from_url, text)
            vocals_path = await asyncio.to_thread(separate_vocals, audio_path)
            await update.message.reply_audio(open(vocals_path, "rb"))
        except Exception as e:
            logging.error(e)
            await update.message.reply_text("❌ حصل خطأ، تأكد إن الرابط صحيح وصالح للتحميل.")
        await msg.delete()

def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))
    app.run_polling()

if __name__ == "__main__":
    main()
