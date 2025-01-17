import os
import logging
from flask import Flask
from telegram import Bot, Update
from telegram.ext import Dispatcher, CommandHandler, CallbackContext
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# Налаштування логування
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# Ідентифікатор таблиці Google Sheets
USER_SHEET_ID = "15Cp8O9FMz4UMxAtGBllC0urHqDozrlzfHNueXc4V5oI"  # Таблиця з аркушем Telegram ID

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

# Функція для запису нового користувача до таблиці
def add_manager_id_to_sheet(user_name, user_id):
    try:
        sheet = client.open_by_key(USER_SHEET_ID).worksheet("Telegram ID")  # Аркуш "Telegram ID"
        data = sheet.get_all_records()

        # Перевіряємо, чи користувач вже є в таблиці
        for row in data:
            if str(row["Telegram ID"]) == str(user_id):  # Перевіряємо по "Telegram ID"
                logger.info(f"Користувач {user_name} (ID: {user_id}) вже є в таблиці.")
                return

        # Додаємо нового користувача
        sheet.append_row([user_id, user_name], value_input_option="USER_ENTERED")
        logger.info(f"Користувача {user_name} (ID: {user_id}) успішно додано в таблицю.")
    except Exception as e:
        logger.error(f"Помилка при записі до таблиці: {e}")

# Перевірка, чи користувач є в базі
def is_user_in_db(user_id):
    try:
        sheet = client.open_by_key(USER_SHEET_ID).worksheet("Telegram ID")
        data = sheet.get_all_records()
        return any(str(row["Telegram ID"]) == str(user_id) for row in data)
    except Exception as e:
        logger.error(f"Помилка перевірки бази даних: {e}")
        return False

# Обробка команди /start
def start(update: Update, context: CallbackContext):
    user_name = update.effective_user.first_name
    user_id = update.effective_user.id
    logger.info(f"Користувач {user_name} (ID: {user_id}) запустив бота.")

    # Перевіряємо чи є в базі
    if is_user_in_db(user_id):
        update.message.reply_text("Ти вже є в базі даних.")
        logger.info(f"Користувач {user_name} вже є в базі.")
    else:
        try:
            add_manager_id_to_sheet(user_name, user_id)
            update.message.reply_text("Тебе успішно додано в таблицю!")
            logger.info(f"Користувача {user_name} (ID: {user_id}) успішно додано.")
        except Exception as e:
            update.message.reply_text("Сталася помилка при додаванні до таблиці.")
            logger.error(f"Помилка додавання до таблиці: {e}")

# Налаштування команди /start
dispatcher.add_handler(CommandHandler("start", start))

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
