"""Save-Bot."""
import logging
import os
import re
from datetime import datetime
from dotenv import load_dotenv
from telebot import TeleBot

load_dotenv()

secret_token = os.getenv('TELEGRAM_TOKEN')
bot = TeleBot(token=secret_token)

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
)


def sanitize_filename(filename: str) -> str:
    """Заменяем недопустимые символы на '-'."""
    return re.sub(r'[<>:"/\\|?*]', '-', filename)


def get_file_extension(file_path: str) -> str:
    """Получаем расширение файла из его имени."""
    return os.path.splitext(file_path)[-1]


def create_directory() -> str:
    """Создает директорию на основе текущей даты и времени."""
    current_date = datetime.now().strftime('%d.%m.%Y %H-%M')
    directory = os.path.join('bot_message', current_date)
    os.makedirs(directory, exist_ok=True)
    return directory


def save_file(file_path: str, data: bytes) -> bool:
    """Сохраняет файл по указанному пути."""
    try:
        with open(file_path, 'wb') as new_file:
            new_file.write(data)
        logging.info(f"Файл сохранен: {file_path}")
        return True
    except IOError as e:
        logging.error(f"Ошибка при сохранении файла {file_path}: {e}")
        return False


def notify_user(chat_id: int, file_name: str) -> None:
    """Сообщает пользователю, что файл был сохранен."""
    bot.send_message(
        chat_id=chat_id, text=f"Файл '{file_name}' успешно сохранен!")


def clean_caption(caption: str) -> str:
    """Очищает заголовок от лишних дефисов с учетом правил русского языка."""
    if not caption:
        return caption

    try:
        caption = re.sub(r'\s*-\s*(?![-]|то|либо|нибудь)|(из-за)', '', caption)
        caption = re.sub(r'-{2,}', '-', caption)
        return caption.strip('- ')
    except re.error as e:
        logging.error(f"Ошибка при очистке заголовка: {e}")
        return caption


def handle_file_download(message, content_type: str) -> None:
    """Общая функция для скачивания и сохранения файлов (фото/видео)."""
    directory = create_directory()
    try:
        file_info = bot.get_file(
            (message.photo[-1].file_id) if (
                content_type == 'photo'
                ) else (message.video.file_id)
        )

        if not file_info.file_path:
            logging.error("Не удалось получить путь к файлу.")
            return

        downloaded_file = bot.download_file(file_info.file_path)

        extension = get_file_extension(file_info.file_path)
        caption = message.caption if content_type == 'photo' else (
            message.caption or (
                f'{content_type}_{datetime.now().strftime("%d-%m-%Y %H-%M")}')
        )

        cleaned_caption = clean_caption(caption)
        file_name = f"{sanitize_filename(cleaned_caption)}{extension}"
        file_path = os.path.join(directory, file_name)

        if save_file(file_path, downloaded_file):
            notify_user(message.chat.id, file_name)
        else:
            remove_empty_directory(directory)
    except Exception as e:
        logging.error(f"Ошибка в процессе скачивания и сохранения файла: {e}")
        bot.send_message(
            chat_id=message.chat.id, text=f"Произошла ошибка: {e}"
        )
        remove_empty_directory(directory)


def remove_empty_directory(directory: str) -> None:
    """Удаляет директорию, если она пуста."""
    try:
        os.rmdir(directory)
        logging.info(f"Директория удалена: {directory}")
    except OSError as e:
        logging.error(f"Ошибка при удалении директории {directory}: {e}")


@bot.message_handler(commands=['start'])
def wake_up(message) -> None:
    """Запуск чат-бота."""
    bot.send_message(chat_id=message.chat.id, text='Бот включен!')


@bot.message_handler(content_types=['photo'])
def get_photo(message) -> None:
    """Сохранение фото из сообщения."""
    handle_file_download(message, 'photo')


@bot.message_handler(content_types=['video'])
def get_video(message) -> None:
    """Сохранение видео из сообщения."""
    handle_file_download(message, 'video')


def main() -> None:
    """Запуск бота."""
    bot.polling(none_stop=True)


if __name__ == '__main__':
    main()
