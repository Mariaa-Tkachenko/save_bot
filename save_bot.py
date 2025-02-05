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
    return re.sub(r'[<>:"/\\|?*\n]', '-', filename)


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
        file_info = get_file_info(message, content_type)
        if not file_info.file_path:
            log_and_notify_error(
                "Не удалось получить путь к файлу.", message.chat.id)
            return

        downloaded_file = bot.download_file(file_info.file_path)
        file_name, file_path = prepare_file_name_and_path(
            file_info, message, directory, content_type)

        if save_file(file_path, downloaded_file):
            notify_user(message.chat.id, file_name)
        else:
            log_and_notify_error(
                f"Ошибка при сохранении файла: {file_name}.", message.chat.id)
            save_error_message(
                directory, f"Ошибка при сохранении файла: {file_name}.")
    except Exception as e:
        handle_download_exception(e, message.chat.id, message, directory)


def get_file_info(message, content_type: str):
    """Получает информацию о файле в зависимости от типа контента."""
    return bot.get_file(
        (
            message.photo[-1].file_id
            ) if (content_type == 'photo') else (message.video.file_id)
    )


def prepare_file_name_and_path(
        file_info, message, directory, content_type: str):
    """Готовит имя файла и путь для сохранения."""
    extension = get_file_extension(file_info.file_path)
    caption = (
        message.caption or (
            f'{content_type}_{datetime.now().strftime("%d.%m.%Y %H:%M")}'))
    cleaned_caption = clean_caption(caption)
    file_name = f"{sanitize_filename(cleaned_caption)}{extension}"
    file_path = os.path.join(directory, file_name)
    return file_name, file_path


def log_and_notify_error(error_message: str, chat_id: int) -> None:
    """Логирует ошибку и отправляет уведомление пользователю."""
    logging.error(error_message)
    bot.send_message(chat_id=chat_id, text=error_message)


def handle_download_exception(e, chat_id, message, directory, file_info=None, content_type='text') -> None:
    """Обрабатывает исключения, возникающие при скачивании файла."""
    if "400" in str(e):
        caption = (
            message.caption or (
                f'{content_type}_{datetime.now().strftime("%d.%m.%Y %H:%M")}'))
        cleaned_caption = clean_caption(caption)
        file_name = f"{sanitize_filename(cleaned_caption)}.txt"
        error_message = f"Файл большой для скачивания, сохранено сообщение: {file_name}"
        log_and_notify_error(error_message, chat_id)
        save_error_message(directory, file_name)
    else:
        log_and_notify_error(f"Ошибка в процессе скачивания и сохранения файла: {e}", chat_id)
        remove_empty_directory(directory)


def save_error_message(directory: str, file_name) -> None:
    """Сохраняет сообщение об ошибке в текстовый файл в указанной директории."""
    error_file_path = os.path.join(directory, file_name)
    try:
        with open(error_file_path, 'w', encoding='utf-8') as error_file:
            error_file.write(file_name)
        logging.info(f"Сообщение об ошибке сохранено в: {error_file_path}")
    except IOError as e:
        logging.error(f"Ошибка при сохранении сообщения об ошибке: {e}")


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
