import os
import logging
from flask import Flask, request, jsonify
from telegram import Bot, Update
from gspread import authorize
from oauth2client.service_account import ServiceAccountCredentials

# Налаштування логування
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# Ініціалізація бота
TOKEN = os.getenv("TELEGRAM_TOKEN")
bot = Bot(token=TOKEN)

# Ініціалізація Flask додатку
app = Flask(__name__)

# Ініціалізація Google Sheets
SHEET_ID = "15Cp8O9FMz4UMxAtGBllC0urHqDozrlzfHNueXc4V5oI"
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_name("service_account.json", scope)
client = authorize(creds)

# Функція для додавання користувача до таблиці
def add_user_to_sheet(chat_id, first_name):
    try:
        # Відкриваємо таблицю
        sheet = client.open_by_key(SHEET_ID).worksheet("Telegram ID")
        all_data = sheet.get_all_records()

        # Перевіряємо, чи вже є користувач у таблиці
        for row in all_data:
            if str(row["ID"]) == str(chat_id):
                logger.info(f"Користувач {first_name} (ID: {chat_id}) вже є у таблиці.")
                return

        # Додаємо нового користувача
        sheet.append_row([chat_id, first_name])
        logger.info(f"Користувача {first_name} (ID: {chat_id}) додано до таблиці.")
    except Exception as e:
        logger.error(f"Помилка при роботі з таблицею: {e}")

# Маршрут для обробки /start
@app.route('/start', methods=['POST'])
def start():
    try:
        data = request.json
        chat_id = data.get("chat_id")
        first_name = data.get("first_name")

        if not chat_id or not first_name:
            return jsonify({"error": "chat_id або first_name відсутні"}), 400

        # Додаємо користувача до таблиці
        add_user_to_sheet(chat_id, first_name)

        # Відповідаємо користувачу
        bot.send_message(chat_id=chat_id, text=f"Привіт, {first_name}! Тебе успішно додано до бази.")
        return jsonify({"status": "success"}), 200
    except Exception as e:
        logger.error(f"Помилка при обробці команди /start: {e}")
        return jsonify({"error": str(e)}), 500
