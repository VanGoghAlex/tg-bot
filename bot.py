import os
import logging
from telegram import Update
from telegram.ext import Updater, CommandHandler, CallbackContext
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

# Ініціалізація Telegram Token
TOKEN = os.getenv("TELEGRAM_TOKEN")

# Функція для запису ID менеджера в Google Таблицю
def add_manager_id_to_sheet(user_name, user_id):
    sheet = client.open_by_key(USER_SHEET_ID).sheet1  # Відкрити таблицю
    existing_ids = set(sheet.col_values(1))  # Отримати всі ID з першої колонки
    
    if str(user_id) not in existing_ids:  # Якщо ID ще немає в таблиці
        sheet.append_row([str(user_id), user_name])  # Додати новий рядок із ID та іменем
        logger.info(f"Додано нового менеджера: {user_name} (ID: {user_id})")
    else:
        logger.info(f"Менеджер {user_name} (ID: {user_id}) вже існує у таблиці")

# Функція для отримання списку менеджерів та їхніх Telegram ID
def get_managers():
    sheet = client.open_by_key(USER_SHEET_ID).sheet1
    data = sheet.get_all_values()[1:]  # Пропускаємо заголовок
    return {row[1]: row[0] for row in data if len(row) >= 2}  # {manager_name: telegram_id}

# Функція для надсилання повідомлень менеджерам
def send_payments(update: Update, context: CallbackContext):
    try:
        sheet = client.open_by_key(DATA_SHEET_ID).worksheet("Пам’ять скрипта по оплатах")
        all_data = sheet.get_all_values()[1:]  # Пропускаємо заголовок

        managers = get_managers()  # Отримуємо список менеджерів та їх ID

        for row in all_data:
            client_name = row[0]  # Колонка F — Клієнт
            manager_name = row[1]  # Колонка G — Менеджер
            month = row[2]  # Колонка H — Місяць
            amount = row[3]  # Колонка I — Сума

            # Формуємо повідомлення
            message = f"Оплата: {client_name}\nМісяць: {month}\nСума: {amount}"

            # Надсилаємо повідомлення, якщо менеджер знайдений
            if manager_name in managers:
                telegram_id = managers[manager_name]
                context.bot.send_message(chat_id=telegram_id, text=message)
                logger.info(f"Повідомлення надіслано менеджеру {manager_name} (ID: {telegram_id})")
            else:
                logger.warning(f"Менеджер {manager_name} не знайдений у таблиці ID користувачів.")
        
        update.message.reply_text("Повідомлення успішно надіслані всім менеджерам.")
    except Exception as e:
        logger.error(f"Сталася помилка під час надсилання повідомлень: {e}")
        update.message.reply_text(f"Сталася помилка: {e}")

# Обробник команди /start
def start(update: Update, context: CallbackContext):
    user_name = update.effective_user.first_name
    user_id = update.effective_user.id
    update.message.reply_text(f"Привіт, {user_name}! Твій Telegram ID: {user_id}")
    
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

    # Додаємо обробник команди /send для надсилання повідомлень менеджерам
    dp.add_handler(CommandHandler("send", send_payments))

    # Запуск бота за допомогою long polling
    updater.start_polling()
    updater.idle()
