import json
import logging
import os
import sys
import time
from logging.handlers import RotatingFileHandler

import requests
import telegram
from dotenv import load_dotenv
from telegram import Bot

from exceptions import ListTypeError, StatusError


load_dotenv()


PRACTICUM_TOKEN = os.getenv('PRACTICUM_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

RETRY_PERIOD = 600
ENDPOINT = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'
HEADERS = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}

HOMEWORK_VERDICTS = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена: у ревьюера есть замечания.'
}


def check_tokens():
    ...


def send_message(bot, message):
    ...


def get_api_answer(timestamp):
    """Отправляет GET-запрос к эндпоинту url API Практикум.Домашка."""
    # в заголовке запроса передать токен авторизации  Authorization: OAuth <token>
    # в гет параметр from date передать метку времени в формате unix time ( 1549962000)


def check_response(response):
    ...


def parse_status(homework):
    ...

    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def main():
    """Основная логика работы бота."""
    logger.debug('Запуск бота')
    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    timestamp = int(time.time())
    error_string = None

    while True:
        try:
            response = get_api_answer(timestamp)
            if response.get('homeworks'):
                message = parse_status(
                    response.get('homeworks')[0]
                )
                send_message(bot, message)
            timestamp = response.get('current_date', timestamp)
            time.sleep(RETRY_PERIOD)

        except Exception as error:
            message = f'Сбой в работе программы: {error}'
            if str(error) != error_string:
                send_message(bot, message=str(error))
                error_string = str(error)
            time.sleep(RETRY_PERIOD)
        else:
            error_string = None


if __name__ == '__main__':
    main()
