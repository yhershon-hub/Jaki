import os
import sys
import asyncio
import anthropic
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters

print("Starting bot...", flush=True)

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY")
RENDER_EXTERNAL_URL = os.environ.get("RENDER_EXTERNAL_URL", "")
PORT = int(os.environ.get("PORT", 10000))

client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("שלום! אני ג'א ג'י, העוזר האישי שלך. שלח לי הודעה ואשמח לעזור.")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_message = update.message.text
    try:
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=1024,
            messages=[{"role": "user", "content": user_message}]
        )
        reply = response.content[0].text
        await update.message.reply_text(reply)
    except Exception as e:
        print(f"Error: {e}", flush=True)
        await update.message.reply_text(f"שגיאה: {str(e)}")

async def main():
    print("Building app...", flush=True)
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

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
  
