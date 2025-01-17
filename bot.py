import os
import logging
from flask import Flask, request
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# Налаштування логування
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Ініціалізація Google Sheets API
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_name("service_account.json", scope)
client = gspread.authorize(creds)

# Вкажіть назву або ID таблиці
SHEET_ID = "15Cp8O9FMz4UMxAtGBllC0urHqDozrlzfHNueXc4V5oI"
SHEET_NAME = "Telegram ID"

# Ініціалізація Telegram бота
TOKEN = os.getenv("TELEGRAM_TOKEN")
application = Application.builder().token(TOKEN).build()

# Flask додаток
app = Flask(__name__)

# Функція для запису даних у Google Sheets
def save_to_google_sheets(user_id, user_name):
    try:
        sheet = client.open_by_key(SHEET_ID).worksheet(SHEET_NAME)
        sheet.append_row([user_id, user_name])  # Додаємо новий рядок
        logger.info(f"Дані записані: {user_id}, {user_name}")
    except Exception as e:
        logger.error(f"Помилка запису до таблиці: {e}")

# Обробник команди /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_name = update.effective_user.first_name
    user_id = update.effective_user.id

    # Зберігаємо дані в таблицю
    save_to_google_sheets(user_id, user_name)

    # Відправляємо відповідь користувачу
    await update.message.reply_text(f"Привіт, {user_name}, приємно познайомитися! Ваш ID ({user_id}) успішно записаний.")

# Додаємо обробник для команди /start
application.add_handler(CommandHandler("start", start))

# Вебхук для прийому оновлень
@app.route(f"/{TOKEN}", methods=["POST"])
def webhook():
    update = Update.de_json(request.get_json(force=True), application.bot)
    application.process_update(update)
    return "OK", 200

# Запуск сервера
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
