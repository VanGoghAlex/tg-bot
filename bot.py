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
data_sheet = client.open_by_key(DATA_SHEET_ID).worksheet("\u0420\u043e\u0437\u0440\u0430\u0445\u0443\u043d\u043a\u0438")

# Отримуємо список менеджерів та їхні Telegram ID
def get_managers():
    data = user_sheet.get_all_values()[1:]  # Пропускаємо заголовок
    return {row[2]: row[0] for row in data if len(row) >= 3 and row[2]}  # {manager_name: telegram_id}

# Відправка повідомлення менеджеру
def send_message(manager_name, message):
    managers = get_managers()
    if manager_name in managers:
        telegram_id = managers[manager_name]
        bot.send_message(chat_id=telegram_id, text=message)
    else:
        logger.warning(f"Менеджер {manager_name} не знайдений у таблиці ID користувачів.")

# Відстеження замальованих клітинок
def check_payments():
    all_data = data_sheet.get_all_values()
    header = all_data[0]
    clients = all_data[1:]

    for row in clients:
        client_name = row[0]
        manager_name = extract_manager_name(client_name)

        for col_index in range(1, len(header)):
            cell_value = row[col_index]
            if is_colored(data_sheet, col_index + 1, clients.index(row) + 2):  # Перевірка кольору клітинки
                month = header[col_index]
                message = f"Отримано оплату від {client_name} за {month}."
                send_message(manager_name, message)

# Функція для перевірки кольору клітинки
def is_colored(sheet, col, row):
    cell = sheet.cell(row, col)
    return cell.text_format and cell.text_format.get('foregroundColor')

# Функція для витягання імені менеджера із назви клієнта
def extract_manager_name(client_name):
    if '(' in client_name and ')' in client_name:
        return client_name.split('(')[-1].split(')')[0].strip()
    return None

if __name__ == "__main__":
    try:
        check_payments()
    except Exception as e:
        logger.error(f"Сталася помилка: {e}")
