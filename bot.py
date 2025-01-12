import os
import logging
from telegram import Update
from telegram.ext import Updater, CommandHandler, CallbackContext
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# Налаштування логування
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# Ідентифікатор таблиці Google Sheets (взяти з URL таблиці)
SHEET_ID = "1G1TvM6BMakQegginA4W8ZVsqTqaflbTMHwWCFG0nvdI"

# Ініціалізація Google Sheets API
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_name("service_account.json", scope)
client = gspread.authorize(creds)

# Ініціалізація Telegram Token
TOKEN = os.getenv("TELEGRAM_TOKEN")

# Функція для запису ID менеджера в Google Таблицю
def add_manager_id_to_sheet(user_name, user_id):
    sheet = client.open_by_key(SHEET_ID).sheet1  # Відкрити таблицю (перший аркуш)
    data = sheet.get_all_values()  # Отримати всі дані таблиці
    existing_ids = [row[0] for row in data]  # Зібрати список існуючих ID
    
    if str(user_id) not in existing_ids:  # Якщо ID ще немає в таблиці
        sheet.append_row([str(user_id), user_name])  # Додати новий рядок із ID та іменем

# Обробник команди /start
def start(update: Update, context: CallbackContext):
    user_name = update.effective_user.first_name
    user_id = update.effective_user.id
    update.message.reply_text(f"Хай, {user_name}! Твій Telegram ID: {user_id}")
    
    # Спроба записати ID в таблицю
    try:
        add_manager_id_to_sheet(user_name, user_id)
        update.message.reply_text("Тебе успішно додано в таблицю!")
    except Exception as e:
        logger.error(f"Помилка при додаванні ID в таблицю: {e}")
        update.message.reply_text(f"Сталася помилка: {e}")

# Основна функція для запуску бота
if __name__ == "__main__":
    updater = Updater(token=TOKEN, use_context=True)
    dp = updater.dispatcher

    # Додаємо обробник команди /start
    dp.add_handler(CommandHandler("start", start))

    # Використання вебхуків із правильною URL-адресою без вказання порту
    public_url = os.getenv('RENDER_EXTERNAL_URL')
    updater.start_webhook(listen="0.0.0.0", url_path=TOKEN)
    updater.bot.set_webhook(f"{public_url}/{TOKEN}")

    updater.idle()
