import os
import logging
from flask import Flask, request
from telegram import Bot, Update
from telegram.ext import Dispatcher, CommandHandler, CallbackContext
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# Налаштування логування
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# Ідентифікатори таблиць Google Sheets
USER_SHEET_ID = "1G1TvM6BMakQegginA4W8ZVsqTqaflbTMHwWCFG0nvdI"  # Таблиця з ID користувачів
DATA_SHEET_ID = "15Cp8O9FMz4UMxAtGBllC0urHqDozrlzfHNueXc4V5oI"  # Таблиця з даними

# Ініціалізація Google Sheets API
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_name("/etc/secrets/service_account.json", scope)
client = gspread.authorize(creds)

# Ініціалізація Telegram бота
TOKEN = os.getenv("TELEGRAM_TOKEN")
bot = Bot(token=TOKEN)

# Flask додаток
app = Flask(__name__)

# Dispatcher для обробки оновлень
dispatcher = Dispatcher(bot, None, workers=0)

# Функція для запису ID менеджера в Google Таблицю
def add_manager_id_to_sheet(user_name, user_id):
    sheet = client.open_by_key(USER_SHEET_ID).sheet1  # Відкрити таблицю
    existing_ids = set(sheet.col_values(1))  # Отримати всі ID з першої колонки
    
    if str(user_id) not in existing_ids:  # Якщо ID ще немає в таблиці
        sheet.append_row([str(user_id), user_name])  # Додати новий рядок із ID та іменем
        logger.info(f"Додано нового менеджера: {user_name} (ID: {user_id})")
    else:
        logger.info(f"Менеджер {user_name} (ID: {user_id}) вже існує у таблиці")

# Функція для обробки команди /start
def start(update: Update, context: CallbackContext):
    user_name = update.effective_user.first_name
    user_id = update.effective_user.id
    update.message.reply_text(f"Привіт, {user_name}! Твій Telegram ID: {user_id}")
    
    # Спроба записати ID в таблицю
    try:
        add_manager_id_to_sheet(user_name, user_id)
        update.message.reply_text("Тебе успішно додано в таблицю!")
    except Exception as e:
        logger.error(f"Помилка при додаванні ID в таблицю: {e}")
        update.message.reply_text(f"Сталася помилка: {e}")

# Додаємо обробник команди /start
dispatcher.add_handler(CommandHandler("start", start))

# Функція для обробки вебхука
@app.route(f'/{TOKEN}', methods=['POST'])
def webhook():
    update = Update.de_json(request.get_json(force=True), bot)
    dispatcher.process_update(update)
    return "OK", 200

# Основна функція запуску
if __name__ == "__main__":
    # Налаштування вебхука
WEBHOOK_URL = f"https://tg-bot-a1zg.onrender.com/{TOKEN}"
bot.set_webhook(WEBHOOK_URL)
    
    # Запуск Flask додатка
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
