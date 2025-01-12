import os
import logging
import gspread
from telegram import Update
from telegram.ext import Updater, CommandHandler, CallbackContext

# Налаштування логування
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# Зчитування токену Telegram і ID таблиці з середовища
TOKEN = os.getenv("TELEGRAM_TOKEN")
SPREADSHEET_ID = os.getenv("SPREADSHEET_ID")
SERVICE_ACCOUNT_FILE = '/etc/secrets/service_account_key.json'

# Підключення до Google Sheets
gc = gspread.service_account(filename=SERVICE_ACCOUNT_FILE)
sheet = gc.open_by_key(SPREADSHEET_ID).sheet1

# Функція для обробки команди /start
def start(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    first_name = update.effective_user.first_name
    message = f"Привіт, {first_name}! Ваш Telegram ID: {user_id}"
    
    # Знаходимо порожній рядок і записуємо ID користувача
    empty_row = len(sheet.get_all_values()) + 1
    sheet.update(f"A{empty_row}", [[first_name, user_id]])

    update.message.reply_text(message)

if __name__ == "__main__":
    updater = Updater(token=TOKEN, use_context=True)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))

    # Запуск бота
    updater.start_polling()
    updater.idle()
