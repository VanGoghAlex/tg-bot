import os
import logging
from telegram import Update
from telegram.ext import Updater, CommandHandler, CallbackContext

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

TOKEN = os.getenv("TELEGRAM_TOKEN")

def start(update: Update, context: CallbackContext):
    update.message.reply_text(f"Хай, {update.effective_user.first_name}! I'm your bot, Голова.")

if __name__ == "__main__":
    updater = Updater(token=TOKEN, use_context=True)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))

    # Використання вебхуків із правильною URL-адресою без вказання порту
    public_url = os.getenv('RENDER_EXTERNAL_URL')
    updater.start_webhook(listen="0.0.0.0", url_path=TOKEN)
    updater.bot.set_webhook(f"{public_url}/{TOKEN}")

    updater.idle()
