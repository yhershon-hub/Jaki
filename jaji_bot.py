#!/usr/bin/env python3
import os
import logging
from datetime import datetime, timedelta
from telegram import Update
from telegram.ext import Application, MessageHandler, CommandHandler, filters, ContextTypes
import anthropic

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY")

conversation_history = {}
MAX_HISTORY = 20

SYSTEM_PROMPT = """אתה ג'א ג'י — עוזר אישי חכם, יעיל ואמין.
אתה מגיב תמיד בשפה שבה פונים אליך.
אתה ישיר, תכליתי, ועושה את העבודה.
כשמבקשים ממך לבצע — בצע, אל תשאל שאלות מיותרות.
כשמשהו לא ברור — שאל שאלה אחת ממוקדת בלבד."""

async def chat_with_jaji(user_id, user_message):
    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
    if user_id not in conversation_history:
        conversation_history[user_id] = []
    conversation_history[user_id].append({"role": "user", "content": user_message})
    if len(conversation_history[user_id]) > MAX_HISTORY * 2:
        conversation_history[user_id] = conversation_history[user_id][-MAX_HISTORY * 2:]
    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=2
