import os
import logging
from flask import Flask, request, jsonify
from telegram import Bot
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# Налаштування логування
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# Змінні оточення
TOKEN = os.getenv("TELEGRAM_TOKEN")  # Telegram токен
USER_SHEET_ID = "1G1TvM6BMakQegginA4W8ZVsqTqaflbTMHwWCFG0nvdI"  # Таблиця з ID користувачів
DATA_SHEET_ID = "15Cp8O9FMz4UMxAtGBllC0urHqDozrlzfHNueXc4V5oI"  # Таблиця з даними

# Перевірка токена
if not TOKEN:
    logger.error("TELEGRAM_TOKEN не знайдено!")
    raise ValueError("TELEGRAM_TOKEN не знайдено!")
else:
    logger.info(f"Токен знайдено: {TOKEN[:5]}...")

# Ініціалізація Telegram бота
try:
    bot = Bot(token=TOKEN)
    logger.info("Telegram бот успішно створений!")
except Exception as e:
    logger.error(f"Помилка ініціалізації Telegram бота: {e}")
    raise

# Ініціалізація Google Sheets API
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_name("/etc/secrets/service_account.json", scope)
client = gspread.authorize(creds)

# Flask додаток
app = Flask(__name__)

@app.route('/send_message', methods=['POST'])
def send_message():
    try:
        # Отримуємо дані з запиту
        data = request.json
        chat_id = data.get("chat_id")
        message = data.get("message")

        if not chat_id or not message:
            return jsonify({"error": "chat_id або message відсутні"}), 400

        bot.send_message(chat_id=chat_id, text=message)
        logger.info(f"Повідомлення надіслано до чату {chat_id}")
        return jsonify({"status": "success"}), 200
    except Exception as e:
        logger.error(f"Помилка відправки повідомлення: {e}")
        return jsonify({"error": str(e)}), 500

# Запуск сервера
if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
