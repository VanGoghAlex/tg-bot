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

# Функція для отримання ID менеджерів
def get_manager_ids():
    try:
        sheet = client.open_by_key(USER_SHEET_ID).sheet1  # Відкрити таблицю з менеджерами
        data = sheet.get_all_records()
        manager_ids = {}
        for row in data:
            manager_ids[row['Name']] = row['ID']  # Маємо зв'язок ім'я менеджера -> ID
        logger.info(f"Отримано ID менеджерів: {manager_ids}")
        return manager_ids
    except Exception as e:
        logger.error(f"Помилка при отриманні ID менеджерів: {e}")
        return {}

# Функція для отримання даних з аркуша "Пам’ять скрипта по оплатах"
def get_payment_data():
    try:
        sheet = client.open_by_key(DATA_SHEET_ID).worksheet("Пам’ять скрипта по оплатах")  # Відкриваємо потрібний аркуш
        data = sheet.get_all_records(head=2)  # Починаємо з другого рядка, де є дані
        logger.info(f"Отримано дані про оплати: {data}")
        return data
    except Exception as e:
        logger.error(f"Помилка при отриманні даних про оплати: {e}")
        return []

# Функція для відправки повідомлень менеджерам
def send_payments_to_managers():
    try:
        # Отримуємо всі дані
        payments = get_payment_data()
        if not payments:
            logger.warning("Немає даних для обробки!")
            return
        
        manager_ids = get_manager_ids()  # Отримуємо ID менеджерів
        
        # Перебираємо записи
        for payment in payments:
            client_name = payment.get('F')  # Клієнт
            manager_name = payment.get('G')  # Менеджер
            month = payment.get('Н')  # Місяць
            amount = payment.get('І')  # Сума

            # Перевіряємо, чи є менеджер в списку з ID
            if manager_name in manager_ids:
                manager_id = manager_ids[manager_name]
                
                # Формуємо повідомлення
                message = f"Привіт, {manager_name}!\n\nОсь інформація по клієнту {client_name}:\n"
                message += f"Місяць: {month}\n"
                message += f"Сума: {amount}\n"
                message += "\nБудь ласка, перевірте платежі та зв'яжіться з клієнтом, якщо потрібно."

                # Відправляємо повідомлення менеджеру
                try:
                    bot.send_message(chat_id=manager_id, text=message)
                    logger.info(f"Повідомлення відправлено менеджеру {manager_name} (ID: {manager_id})")
                except Exception as e:
                    logger.error(f"Не вдалося відправити повідомлення менеджеру {manager_name}: {e}")
            else:
                logger.warning(f"Менеджер {manager_name} не знайдений у списку ID")
    except Exception as e:
        logger.error(f"Помилка при відправці повідомлень менеджерам: {e}")

# Обробка команди /start
def start(update: Update, context: CallbackContext):
    user_name = update.effective_user.first_name
    user_id = update.effective_user.id
    logger.info(f"Користувач {user_name} (ID: {user_id}) запустив бота.")
    
    # Перевірка, чи є користувач в таблиці
    if is_user_in_db(user_id):
        update.message.reply_text(f"Ти вже є в базі даних. Повідомлення не буде повторно надіслано.")
        logger.info(f"Користувач {user_name} вже є в базі даних.")
    else:
        try:
            add_manager_id_to_sheet(user_name, user_id)
            update.message.reply_text("Тебе успішно додано в таблицю!")
            logger.info(f"Користувач {user_name} (ID: {user_id}) успішно додано в таблицю.")
        except Exception as e:
            update.message.reply_text(f"Сталася помилка при додаванні тебе в таблицю: {e}")
            logger.error(f"Помилка при додаванні {user_name} (ID: {user_id}) в таблицю: {e}")

# Запускаємо функцію відправки повідомлень
send_payments_to_managers()
