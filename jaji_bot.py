import os
import anthropic
from telegram import Update
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY")

client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

def start(update: Update, context: CallbackContext):
    update.message.reply_text("שלום! אני ג'א ג'י, העוזר האישי שלך. שלח לי הודעה ואשמח לעזור.")

def handle_message(update: Update, context: CallbackContext):
    user_message = update.message.text
    try:
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=1024,
            messages=[{"role": "user", "content": user_message}]
        )
        reply = response.content[0].text
        update.message.reply_text(reply)
    except Exception as e:
        update.message.reply_text(f"שגיאה: {str(e)}")

def main():
    updater = Updater(token=TELEGRAM_TOKEN, use_context=True)
    dp = updater.dispatcher
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_message))
    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()
