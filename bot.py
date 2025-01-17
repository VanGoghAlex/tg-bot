import os
import logging
from flask import Flask, request
from telegram import Bot, Update
from telegram.ext import Application, CommandHandler, ContextTypes

# Налаштування логування
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

# Ініціалізація Flask
app = Flask(__name__)

# Telegram Token
TOKEN = "7618878733:AAEnOG6qUZTDAb3FuycNtbUmWlMnbi4Uafc"

# Ініціалізація Telegram Application
application = Application.builder().token(TOKEN).build()


# Обробник для команди /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_name = update.effective_user.first_name
    user_id = update.effective_user.id
    logger.info(f"Користувач {user_name} (ID: {user_id}) запустив бота.")
    await update.message.reply_text(f"Привіт, {user_name}! Ваш Telegram ID: {user_id}")


# Додати обробник для команди /start
application.add_handler(CommandHandler("start", start))


# Маршрут для обробки вебхуків
@app.route(f"/{TOKEN}", methods=["POST"])
def webhook():
    try:
        # Отримання оновлення від Telegram
        json_update = request.get_json(force=True)
        update = Update.de_json(json_update, application.bot)
        logger.info(f"Отримано оновлення: {json_update}")
        
        # Обробка оновлення через Application
        application.update_queue.put_nowait(update)
        return "OK", 200
    except Exception as e:
        logger.error(f"Помилка при обробці вебхука: {e}")
        return "Internal Server Error", 500


# Головна сторінка для перевірки роботи сервера
@app.route("/", methods=["GET"])
def index():
    return "Сервер працює! Telegram Bot готовий до роботи.", 200


# Запуск Flask сервера
if __name__ == "__main__":
    PORT = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=PORT)
