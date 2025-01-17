import os
import logging
from flask import Flask, request, jsonify
from telegram import Bot

# Налаштування логування
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# Отримання токена
TOKEN = os.getenv("TELEGRAM_TOKEN")
if not TOKEN:
    logger.error("TELEGRAM_TOKEN не знайдено!")
    raise ValueError("TELEGRAM_TOKEN не знайдено!")

# Ініціалізація Telegram бота
try:
    bot = Bot(token=TOKEN)
    logger.info("Telegram бот успішно ініціалізований!")
except Exception as e:
    logger.error(f"Помилка ініціалізації бота: {e}")
    raise

# Flask додаток
app = Flask(__name__)

# Ендпоінт для перевірки стану сервера
@app.route('/', methods=['GET'])
def index():
    return "Сервер працює!", 200

# Ендпоінт для надсилання повідомлень
@app.route('/send_message', methods=['POST'])
def send_message():
    try:
        # Отримання даних із запиту
        data = request.json
        chat_id = data.get("chat_id")
        message = data.get("message")

        # Перевірка вхідних даних
        if not chat_id or not message:
            return jsonify({"error": "chat_id або message відсутні"}), 400

        # Надсилання повідомлення
        bot.send_message(chat_id=chat_id, text=message)
        logger.info(f"Повідомлення успішно надіслано до чату {chat_id}")
        return jsonify({"status": "success"}), 200
    except Exception as e:
        logger.error(f"Помилка при надсиланні повідомлення: {e}")
        return jsonify({"error": str(e)}), 500

# Запуск сервера
if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
