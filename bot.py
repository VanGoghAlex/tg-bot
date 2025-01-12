import os
import logging
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from telegram import Bot

# Налаштування логування
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# Ідентифікатори таблиць
USER_SHEET_ID = "1G1TvM6BMakQegginA4W8ZVsqTqaflbTMHwWCFG0nvdI"  # Таблиця з ID користувачів
DATA_SHEET_ID = "15Cp8O9FMz4UMxAtGBllC0urHqDozrlzfHNueXc4V5oI"  # Таблиця з даними

# Підключення до Google Sheets
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_name("/etc/secrets/service_account.json", scope)
client = gspread.authorize(creds)

# Підключення до Telegram Bot
TOKEN = os.getenv("TELEGRAM_TOKEN")
bot = Bot(token=TOKEN)

# Отримання таблиць
user_sheet = client.open_by_key(USER_SHEET_ID).sheet1
data_sheet = client.open_by_key(DATA_SHEET_ID).worksheet("Пам’ять скрипта по оплатах")

# Отримуємо список менеджерів та їхні Telegram ID
def get_managers():
    data = user_sheet.get_all_values()[1:]  # Пропускаємо заголовок
    return {row[1]: row[0] for row in data if len(row) >= 3 and row[1]}  # {manager_name: telegram_id}

# Відправка повідомлення менеджеру
def send_message(manager_name, message):
    managers = get_managers()
    if manager_name in managers:
        telegram_id = managers[manager_name]
        bot.send_message(chat_id=telegram_id, text=message)
    else:
        logger.warning(f"Менеджер {manager_name} не знайдений у таблиці ID користувачів.")

# Перевірка оплат і надсилання повідомлень
def check_payments():
    all_data = data_sheet.get_all_values()[1:]  # Пропускаємо заголовок
    sent_payments = set()  # Зберігаємо вже надіслані повідомлення

    for row in all_data:
        client_name = row[0]  # Колонка F — Клієнт
        manager_name = row[1]  # Колонка G — Менеджер
        month = row[2]  # Колонка H — Місяць
        amount = row[3]  # Колонка I — Сума

        # Унікальний ключ для перевірки дублювання
        payment_key = f"{client_name}-{manager_name}-{month}-{amount}"

        if payment_key not in sent_payments:  # Якщо такого повідомлення ще не було
            message = f"Оплата: {client_name}\nМісяць: {month}\nСума: {amount}"
            send_message(manager_name, message)
            sent_payments.add(payment_key)  # Додаємо ключ у пам'ять
        else:
            logger.info(f"Повідомлення для {payment_key} вже було надіслано.")

if __name__ == "__main__":
    try:
        check_payments()
    except Exception as e:
        logger.error(f"Сталася помилка: {e}")
