import os
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text('Привіт!')

    # Отримуємо ID чату
    chat_id = update.message.chat.id

    # Відображаємо ID у консолі сервера
    print(f"Chat ID: {chat_id}")


def main():
    # Отримання токена із змінної середовища
    TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
    
    application = Application.builder().token(TOKEN).build()

    # Додайте обробник команди /start
    start_handler = CommandHandler('start', start)
    application.add_handler(start_handler)

    # Запуск бота
    application.run_polling()

if __name__ == '__main__':
    main()
