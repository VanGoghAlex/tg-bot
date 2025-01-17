import os
import logging
from flask import Flask, request, jsonify
from telegram import Bot

# Налаштування логування
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# Отримуємо токен Telegram бота з оточення (або додайте його вручну)
TOKEN = os.getenv("TELEGRAM_TOKEN")  # Якщо немає в оточенні, використовуйте: TOKEN = "ВАШ_ТОКЕН"
if not TOKEN:
    raise ValueError("Не задано TELEGRAM_TOKEN!")

# Ініціалізація Telegram бота
bot = Bot(token=TOKEN)

# Ініціалізація Flask-додатка
app = Flask(__name__)

# Маршрут для перевірки стану сервера
@app.route('/', methods=['GET'])
def index():
    return "Сервер працює!", 200

# Ендпоінт для надсилання повідомлень
@app.route('/send_message', methods=['POST'])
def send_message():
    try:
        # Отримуємо дані з POST-запиту
        data = request.json
        chat_id = data.get("chat_id")  # ID чату або користувача Telegram
        message = data.get("message")  # Повідомлення для надсилання

        # Перевірка наявності даних
        if not chat_id or not message:
            return jsonify({"error": "chat_id або message відсутні"}), 400

        # Відправляємо повідомлення через Telegram
        bot.send_message(chat_id=chat_id, text=message)
        logger.info(f"Повідомлення надіслано до чату {chat_id}")
        return jsonify({"status": "success"}), 200
    except Exception as e:
        logger.error(f"Помилка відправки повідомлення: {e}")
        return jsonify({"error": str(e)}), 500

# Запуск сервера
if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))  # Порт задається автоматично Render.com
    app.run(host='0.0.0.0', port=port)
