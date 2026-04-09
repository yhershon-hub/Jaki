import os
import sys
import asyncio
import anthropic
import speech_recognition as sr
import pytz
from datetime import datetime
from gtts import gTTS
from pydub import AudioSegment
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters

print("Starting bot...", flush=True)

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY")
RENDER_EXTERNAL_URL = os.environ.get("RENDER_EXTERNAL_URL", "")
PORT = int(os.environ.get("PORT", 10000))

client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

WAKE_PHRASES = ["הי ג'א ג'י", "היי ג'א ג'י", "הי גא גי", "היי גא גי"]
WAKE_REPLY = "הי! אני כאן. איך אפשר לעזור?"

def get_system_prompt():
    tz = pytz.timezone("Asia/Jerusalem")
    now = datetime.now(tz)
    days_he = ["שני", "שלישי", "רביעי", "חמישי", "שישי", "שבת", "ראשון"]
    months_he = ["ינואר", "פברואר", "מרץ", "אפריל", "מאי", "יוני",
                 "יולי", "אוגוסט", "ספטמבר", "אוקטובר", "נובמבר", "דצמבר"]
    day_name = days_he[now.weekday()]
    month_name = months_he[now.month - 1]
    formatted_datetime = f"יום {day_name}, {now.day} ב{month_name} {now.year}, שעה {now.strftime('%H:%M')}"
    return (
        f"You are ג'א ג'י (Ja Ji), a friendly personal assistant on Telegram. "
        f"You speak Hebrew by default. "
        f"The current date and time is: {formatted_datetime}. "
        f"Always use this when asked about the date or time."
    )

def send_to_claude(text):
    response = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=1024,
        system=get_system_prompt(),
        messages=[{"role": "user", "content": text}]
    )
    return response.content[0].text

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("שלום! אני ג'א ג'י, העוזר האישי שלך. שלח לי הודעה ואשמח לעזור.")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_message = update.message.text

    if user_message.strip() in WAKE_PHRASES:
        await update.message.reply_text(WAKE_REPLY)
        return

    try:
        reply = send_to_claude(user_message)
        await update.message.reply_text(reply)
    except Exception as e:
        print(f"Error: {e}", flush=True)
        await update.message.reply_text(f"שגיאה: {str(e)}")

async def handle_voice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    ogg_path = "/tmp/voice_input.ogg"
    wav_path = "/tmp/voice_input.wav"
    mp3_path = "/tmp/voice_reply.mp3"

    try:
        voice_file = await update.message.voice.get_file()
        await voice_file.download_to_drive(ogg_path)

        audio = AudioSegment.from_ogg(ogg_path)
        audio.export(wav_path, format="wav")

        recognizer = sr.Recognizer()
        with sr.AudioFile(wav_path) as source:
            audio_data = recognizer.record(source)
        transcribed_text = recognizer.recognize_google(audio_data, language="he-IL")

    except Exception as e:
        print(f"Transcription error: {e}", flush=True)
        await update.message.reply_text("לא הצלחתי להבין את ההודעה הקולית. אפשר לנסות שוב?")
        for path in [ogg_path, wav_path, mp3_path]:
            if os.path.exists(path):
                os.remove(path)
        return

    if transcribed_text.strip() in WAKE_PHRASES:
        reply_text = WAKE_REPLY
    else:
        try:
            reply_text = send_to_claude(transcribed_text)
        except Exception as e:
            print(f"Claude error: {e}", flush=True)
            await update.message.reply_text(f"שגיאה: {str(e)}")
            for path in [ogg_path, wav_path, mp3_path]:
                if os.path.exists(path):
                    os.remove(path)
            return

    try:
        tts = gTTS(text=reply_text, lang="iw")
        tts.save(mp3_path)
        with open(mp3_path, "rb") as audio_file:
            await update.message.reply_voice(voice=audio_file)
    except Exception as e:
        print(f"TTS/send error: {e}", flush=True)
        await update.message.reply_text(reply_text)
    finally:
        for path in [ogg_path, wav_path, mp3_path]:
            if os.path.exists(path):
                os.remove(path)

async def main():
    print("Building app...", flush=True)
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_handler(MessageHandler(filters.VOICE, handle_voice))

    webhook_url = f"{RENDER_EXTERNAL_URL}/webhook"
    print(f"Setting webhook to: {webhook_url}", flush=True)

    await app.bot.set_webhook(url=webhook_url)

    async with app:
        await app.start()
        print("Bot is running!", flush=True)

        from aiohttp import web
        async def health(request):
            return web.Response(text="OK")

        async def webhook_handler(request):
            data = await request.json()
            update = Update.de_json(data, app.bot)
            await app.process_update(update)
            return web.Response(text="OK")

        aio_app = web.Application()
        aio_app.router.add_get("/", health)
        aio_app.router.add_post("/webhook", webhook_handler)

        runner = web.AppRunner(aio_app)
        await runner.setup()
        site = web.TCPSite(runner, "0.0.0.0", PORT)
        await site.start()
        print(f"Listening on port {PORT}", flush=True)

        await asyncio.Event().wait()

if __name__ == "__main__":
    asyncio.run(main())
