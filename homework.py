import logging
import time
import requests
import telegram
from telegram import Bot
from dotenv import load_dotenv

load_dotenv()


class ApiResponseException(Exception):
    """Ошибка при запросе к API."""

    def __str__(self):
        """Ошибка в запросе к API."""
        return "Ошибка при запросе к API."


class HomeworkError(Exception):
    """Неправильно заполненный словарь homework."""

    def __str__(self):
        """Ошибка в заполнении словаря."""
        return "Неправильно заполненный словарь homework."


PRACTICUM_TOKEN = "y0_AgAAAABaTRspAAYckQAAAADWvN4nUKVS85jXQryyrLUN3v3KFdNMw-o"
TELEGRAM_TOKEN = "5954457997:AAHobyRY-FrJ5GoTjRHNfieATqSmUeURBiU"
TELEGRAM_CHAT_ID = "228023007"

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
    if any(
        [
            PRACTICUM_TOKEN is None,
            TELEGRAM_TOKEN is None,
            TELEGRAM_CHAT_ID is None,
        ]
    ):
        logger.debug("Не хватает переменных окружения")
        return False
    return True


def send_message(bot: Bot, message):
    """
    Отправляет сообщение messagе через бота - bot.
    Логируется успешную отправку сообщения или ошибку.
    """
    try:
        bot.send_message(TELEGRAM_CHAT_ID, message)
        logger.debug("Бот отправляет сообщение")
    except Exception:
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
        homeworks_update = api_answer.json()
    except Exception:
        logger.error("Не удалось получить данные")
    return homeworks_update


def check_response(response):
    """Провереряет ответ API на корректность."""
    if not isinstance(response, dict) or not isinstance(
        response.get("homeworks"), list
    ):
        raise TypeError
    return response


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
    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    if check_tokens():
        logger.debug("Запуск бота")
        timestamp = int(time.time())
        while True:
            try:
                api_response = get_api_answer(timestamp)
                homeworks_update = check_response(api_response)
                homeworks = homeworks_update.get("homeworks")
                if homeworks:
                    send_message(bot, parse_status(homeworks[0]))
                timestamp = homeworks_update.get("current_date", timestamp)
                logger.debug("Засыпаем")
                time.sleep(RETRY_PERIOD)

            except Exception as error:
                message = f"Сбой в работе программы: {error}"
                logger.error(error, exc_info=True)
                send_message(bot, message)
                time.sleep(RETRY_PERIOD)
    else:
        logger.critical("Не хватает переменных окружения")


if __name__ == "__main__":
    main()
