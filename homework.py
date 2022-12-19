import logging
import sys
import os
import time
import requests
import telegram
from telegram import Bot, TelegramError
from dotenv import load_dotenv
from exceptions import ApiResponseException, HomeworkError

load_dotenv()


PRACTICUM_TOKEN = os.getenv('PRACTICUM_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

RETRY_PERIOD = 600
ENDPOINT = "https://practicum.yandex.ru/api/user_api/homework_statuses/"
HEADERS = {"Authorization": f"OAuth {PRACTICUM_TOKEN}"}

HOMEWORK_VERDICTS = {
    "approved": "Работа проверена: ревьюеру всё понравилось. Ура!",
    "reviewing": "Работа взята на проверку ревьюером.",
    "rejected": "Работа проверена: у ревьюера есть замечания.",
}

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
file_handler = logging.FileHandler("main.log")
file_handler.setFormatter(
    logging.Formatter("%(asctime)s : [%(levelname)s] : %(name)s : %(message)s")
)
logger.addHandler(file_handler)


def check_tokens():
    """Провереряет доступность переменных окружения."""
    return all((PRACTICUM_TOKEN, TELEGRAM_TOKEN, TELEGRAM_CHAT_ID))


def send_message(bot: Bot, message):
    """
    Отправляет сообщение messagе через бота - bot.
    Логируется успешную отправку сообщения или ошибку.
    """
    try:
        bot.send_message(TELEGRAM_CHAT_ID, message)
        logger.debug("Бот отправляет сообщение")
    except TelegramError:
        logger.error("Не удалось отправить сообщение")


def get_api_answer(timestamp):
    """Отправляет GET-запрос к эндпоинту url API Практикум.Домашка."""
    try:
        api_answer = requests.get(
            ENDPOINT, headers=HEADERS, params={"from_date": timestamp}
        )
    except Exception:
        raise ApiResponseException
    if api_answer.status_code != requests.codes.ok:
        raise ApiResponseException
    try:
        return api_answer.json()
    except Exception:
        raise ApiResponseException("Не удалось получить данные")


def check_response(response):
    """Провереряет ответ API на корректность."""
    if not isinstance(response, dict):
        raise TypeError("Ответ не словарь")
    logger.info("Получаем homeworks")
    homeworks = response.get("homeworks")
    if 'homeworks' not in response or 'current_date' not in response:
        raise KeyError("Пустой ответ от API")
    if not isinstance(homeworks, list):
        raise TypeError("Homeworks не является списком")
    return homeworks


def parse_status(homework):
    """Вывод статуса конкретной домашней работы."""
    homework_name = homework.get("homework_name", None)
    homework_status = homework.get("status", None)
    verdict = HOMEWORK_VERDICTS.get(homework_status)
    if homework_name is None or homework_status not in HOMEWORK_VERDICTS:
        raise HomeworkError
    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def main():
    """Основная логика работы бота."""
    if not check_tokens():
        logging.critical(
            "Проверьте количество переменных окружения"
        )
        sys.exit('Отсутсвуют переменные окружения')
    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    while True:
        try:
            logger.debug("Запуск бота")
            timestamp = int(time.time())
            response = get_api_answer(timestamp)
            homeworks = check_response(response)
            if homeworks:
                homework_status = parse_status(homeworks[0])
                send_message(bot, homework_status)
                if homework_status is None:
                    logger.debug("Новый статус не обнаружен")
            timestamp = response.get('current_date', timestamp)
            logger.debug("Засыпаем")
        except Exception as error:
            message = f"Сбой в работе программы: {error}"
            logger.error(message, exc_info=True)
        finally:
            time.sleep(RETRY_PERIOD)


if __name__ == "__main__":
    main()
