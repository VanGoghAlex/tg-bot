import os
import logging
from flask import Flask, request
from telegram import Bot, Update
from telegram.ext import Application, CommandHandler, CallbackContext
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
if not TOKEN:
    logger.error("TELEGRAM_TOKEN не знайдено!")
    raise ValueError("TELEGRAM_TOKEN не знайдено!")
bot = Bot(token=TOKEN)

# Flask додаток
app = Flask(__name__)

# Створюємо Telegram Application
application = Application.builder().token(TOKEN).build()

# Функція для обробки команди /start
async def start(update: Update, context: CallbackContext):
    user_name = update.effective_user.first_name
    user_id = update.effective_user.id
    logger.info(f"Користувач {user_name} (ID: {user_id}) запустив бота.")

    # Відкриття таблиці та перевірка наявності користувача
    try:
        sheet = client.open_by_key(DATA_SHEET_ID).worksheet("Telegram ID")
        records = sheet.get_all_records()

        if any(record['Telegram ID'] == str(user_id) for record in records):
            await update.message.reply_text("Ти вже є в базі даних.")
            logger.info(f"Користувач {user_name} вже є в таблиці.")
        else:
            sheet.append_row([user_id, user_name])
            await update.message.reply_text("Тебе успішно додано в таблицю!")
            logger.info(f"Користувач {user_name} (ID: {user_id}) доданий до таблиці.")
    except Exception as e:
        await update.message.reply_text("Виникла помилка при доступі до таблиці.")
        logger.error(f"Помилка доступу до таблиці: {e}")

# Додаємо команду /start до Application
application.add_handler(CommandHandler("start", start))

# Запуск сервера Flask
@app.route('/', methods=['GET'])
def index():
    return "Сервер працює!", 200

@app.route(f"/{TOKEN}", methods=['POST'])
def webhook():
    """Обробляє вхідні запити від Telegram."""
    update = Update.de_json(request.get_json(force=True), bot)
    application.update_queue.put_nowait(update)
    return "OK", 200

# Запуск Flask та Telegram Application
if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
