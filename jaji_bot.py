import os
import anthropic
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, filters
from flask import Flask, request

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY")
RAILWAY_PUBLIC_DOMAIN = os.environ.get("RAILWAY_PUBLIC_DOMAIN", "")
PORT = int(os.environ.get("PORT", 8080))

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
        await update.message.reply_text(f"שגיאה: {str(e)}")

def main():
    app = Application.builder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    webhook_url = f"https://{RAILWAY_PUBLIC_DOMAIN}/webhook"
    app.run_webhook(
        listen="0.0.0.0",
        port=PORT,
        webhook_url=webhook_url,
        url_path="/webhook"
    )

if __name__ == "__main__":
    main()
