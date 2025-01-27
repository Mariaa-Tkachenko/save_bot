import logging
import os
import re
from datetime import datetime

from dotenv import load_dotenv
from telebot import TeleBot


load_dotenv()

secret_token = os.getenv('TELEGRAM_TOKEN')
chat_token = os.getenv('TELEGRAM_CHAT_ID')
bot = TeleBot(token=secret_token)
chat_id = TeleBot(token=chat_token)

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
)


def sanitize_filename(filename):
    """Заменяем недопустимые символы на '-'."""
    return re.sub(r'[<>:"/\\|?*]', '-', filename)


@bot.message_handler(commands=['start'])
def wake_up(message):
    """Запуск чат-бота."""
    chat_id = message.chat.id

    bot.send_message(
        chat_id=chat_id,
        text='Бот включен!',
    )


@bot.message_handler(content_types=['photo'])
def get_photo(message):
    """Сохранение фото из сообщения."""
    current_date = datetime.now()
    date_str = f'{current_date.day}.{current_date.month}.{current_date.year} {current_date.hour}-{current_date.minute}'

    directory = os.path.join('bot_message', date_str)
    os.makedirs(directory, exist_ok=True)
    file_path = os.path.join(directory, f"{message.photo[-1].file_id}.png")

    if message.caption:
        file_name = f"{sanitize_filename(message.caption)}.png"
    else:
        file_name = f"photo_{date_str}.png"

    file_path = os.path.join(directory, file_name)

    file_info = bot.get_file(message.photo[-1].file_id)
    downloaded_file = bot.download_file(file_info.file_path)

    with open(file_path, 'wb') as new_file:
        new_file.write(downloaded_file)


@bot.message_handler(content_types=['video'])
def get_video(message):
    """Сохранение видео из сообщения."""
    current_date = datetime.now()
    date_str = f'{current_date.day}.{current_date.month}.{current_date.year} {current_date.hour}-{current_date.minute}'

    directory = os.path.join('bot_message', date_str)
    os.makedirs(directory, exist_ok=True)
    file_path = os.path.join(directory, f"{message.video.file_id}.mp4")

    if message.caption:

        file_name = f"{sanitize_filename(message.caption)}.mp4"
    else:
        file_name = f"video_{date_str}.mp4"

    file_path = os.path.join(directory, file_name)

    file_info = bot.get_file(message.video.file_id)
    downloaded_file = bot.download_file(file_info.file_path)

    with open(file_path, 'wb') as new_file:
        new_file.write(downloaded_file)


def main():
    bot.polling(none_stop=True)


if __name__ == '__main__':
    main()