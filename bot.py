@app.route('/send_message', methods=['POST'])
def send_message():
    try:
        # Отримуємо дані з запиту
        data = request.json
        chat_id = data.get("chat_id")  # ID менеджера
        message = data.get("message")  # Повідомлення

        if not chat_id or not message:
            return jsonify({"error": "chat_id або message відсутні"}), 400

        # Відправляємо повідомлення через Telegram
        bot.send_message(chat_id=chat_id, text=message)
        logger.info(f"Повідомлення надіслано до чату {chat_id}")
        return jsonify({"status": "success"}), 200
    except Exception as e:
        logger.error(f"Помилка відправки повідомлення: {e}")
        return jsonify({"error": str(e)}), 500
