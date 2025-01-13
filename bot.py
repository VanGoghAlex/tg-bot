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
    sheet = client.open_by_key(USER_SHEET_ID).sheet1  # Відкрити таблицю з менеджерами
    data = sheet.get_all_records()
    manager_ids = {}
    for row in data:
        manager_ids[row['Name']] = row['ID']  # Маємо зв'язок ім'я менеджера -> ID
    return manager_ids

# Функція для отримання даних з аркуша "Пам’ять скрипта по оплатах"
def get_payment_data():
    sheet = client.open_by_key(DATA_SHEET_ID).worksheet("Пам’ять скрипта по оплатах")  # Відкриваємо потрібний аркуш
    data = sheet.get_all_records()
    return data

# Функція для відправки повідомлень менеджерам
def send_payments_to_managers():
    # Отримуємо всі дані
    payments = get_payment_data()
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

# Функція для обробки команди /start
def start(update: Update, context: CallbackContext):
    user_name = update.effective_user.first_name
    user_id = update.effective_user.id
    update.message.reply_text(f"Привіт, {user_name}! Твій Telegram ID: {user_id}")

    # Перевірка наявності ID користувача в таблиці
    sheet = client.open_by_key(USER_SHEET_ID).sheet1
    existing_ids = set(sheet.col_values(1))  # Отримуємо всі ID з першої колонки
    
    if str(user_id) in existing_ids:  # Якщо ID вже є в таблиці, не надсилаємо повторно повідомлення
        update.message.reply_text("Ти вже є в базі даних. Повідомлення не буде повторно надіслано.")
    else:
        # Спроба записати ID в таблицю
        try:
            add_manager_id_to_sheet(user_name, user_id)
            update.message.reply_text("Тебе успішно додано в таблицю!")
        except Exception as e:
            logger.error(f"Помилка при додаванні ID в таблицю: {e}")
            update.message.reply_text(f"Сталася помилка: {e}")

# Функція для запису ID менеджера в Google Таблицю
def add_manager_id_to_sheet(user_name, user_id):
    sheet = client.open_by_key(USER_SHEET_ID).sheet1  # Відкрити таблицю
    existing_ids = set(sheet.col_values(1))  # Отримати всі ID з першої колонки
    
    if str(user_id) not in existing_ids:  # Якщо ID ще немає в таблиці
        sheet.append_row([str(user_id), user_name])  # Додати новий рядок із ID та іменем
        logger.info(f"Додано нового менеджера: {user_name} (ID: {user_id})")
    else:
        logger.info(f"Менеджер {user_name} (ID: {user_id}) вже існує у таблиці")

# Додаємо обробник команди /start
dispatcher.add_handler(CommandHandler("start", start))

# Функція для обробки вебхука
@app.route(f'/{TOKEN}', methods=['POST'])
def webhook():
    update = Update.de_json(request.get_json(force=True), bot)
    dispatcher.process_update(update)
    send_payments_to_managers()  # Викликаємо функцію відправки повідомлень
    return "OK", 200

# Основна функція запуску
if __name__ == "__main__":
    # Налаштування вебхука
    WEBHOOK_URL = f"https://tg-bot-a1zg.onrender.com/{TOKEN}"
    bot.set_webhook(WEBHOOK_URL)

    # Запуск Flask додатка
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
