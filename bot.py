import os
import logging
from telegram import Bot, Update
from telegram.ext import Updater, CommandHandler, CallbackContext

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

TOKEN = os.getenv("TELEGRAM_TOKEN")

def start(update: Update, context: CallbackContext):
    update.message.reply_text(f"Hello, {update.effective_user.first_name}! I'm your bot.")

if __name__ == "__main__":
    updater = Updater(token=TOKEN, use_context=True)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))

    updater.start_polling()
    updater.idle()
