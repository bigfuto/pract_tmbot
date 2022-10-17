import telegram
import requests
import logging
import sys
import ydb
import boto3

from http import HTTPStatus

from exceptions import (
    CriticalException,
    ResponseCodeException,
    FieldTypeException,
    FieldException,
    EmptyFieldException,
    SendMessageException,
    SendRequestException
)
from constants import (
    DB_FIELDS,
    KEYS,
    TOKENS,
    ENDPOINTS,
    S3_FIELDS,
    HEADERS
)

# Логгер
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
handler = logging.StreamHandler()
formatter = logging.Formatter(
    '%(asctime)s [%(funcName)s:%(lineno)d] [%(levelname)s] %(message)s'
)
handler.setFormatter(formatter)
logger.addHandler(handler)

# Подключение к YDB
driver = ydb.Driver(
    endpoint=ENDPOINTS['YDB_ENDPOINT'],
    database=ENDPOINTS['YDB_DATABASE'],
)
driver.wait(fail_fast=True, timeout=5)
pool = ydb.SessionPool(driver)

# Подключение к Object Storage
session = boto3.session.Session()
s3 = session.client(
    service_name='s3',
    endpoint_url=ENDPOINTS['S3_ENDPOINT'],
    aws_access_key_id=TOKENS['AWS_ACCESS_KEY_ID'],
    aws_secret_access_key=TOKENS['AWS_SECRET_ACCESS_KEY'],
)


def read_s3(field) -> str:
    """Читаем сообщение об ошибке из файла."""
    bites = b'\x00'
    for key in s3.list_objects(Bucket=S3_FIELDS['BUCKET'])['Contents']:
        if key['Key'] == field:
            bites = s3.get_object(
                Bucket=S3_FIELDS['BUCKET'], Key=field
            )['Body'].read()
    logger.debug('Сообщение об ошибке успешно прочитано.')
    return str(bites, 'UTF-8')


def write_s3(field, text) -> None:
    """Записываем сообщение об ошибке в файл."""
    s3.put_object(Bucket=S3_FIELDS['BUCKET'], Key=field, Body=text)
    logger.debug('Сообщение об ошибке успешно записано.')


def send_message(bot, message) -> None:
    """Отправляем сообщение в чат."""
    try:
        logger.info('Начали отправку сообщения')
        bot.send_message(
            TOKENS['TELEGRAM_CHAT_ID'],
            text=message[:255]
        )
        logger.info(f'Сообщение с текстом: "{message}" успешно отправлено.')
    except Exception as error:
        logger.error(SendMessageException(error))


def get_api_answer(current_timestamp) -> dict:
    """Делаем запрос к API Практикум.Домашка."""
    params = {'from_date': current_timestamp}
    logger.info('Отправляем запрос к эндпоинту')
    try:
        homework_statuses = requests.get(
            ENDPOINTS['YP_ENDPOINT'], headers=HEADERS, params=params
        )
    except Exception as error:
        raise SendRequestException(error)
    if homework_statuses.status_code != HTTPStatus.OK:
        raise ResponseCodeException(
            homework_statuses.status_code, ENDPOINTS['YP_ENDPOINT']
        )
    logger.debug('Ответ от API успешно получен.')
    return homework_statuses.json()


def check_response(response) -> list:
    """Проверяем ответ API на корректность."""
    if not isinstance(response, dict):
        raise FieldTypeException(dict, type(response))
    logger.debug('Ответ от API имеет правильный формат')
    for field in KEYS['RESPONSE_KEYS'].values():
        if field not in response:
            raise FieldException(field)
    logger.debug('В словаре есть требуемые ключи')
    if not isinstance(response[KEYS['RESPONSE_KEYS']['BASIC']], list):
        raise FieldTypeException(
            list, type(response[KEYS['RESPONSE_KEYS']['BASIC']])
        )
    logger.debug('Ответ от API имеет правильный формат')
    if not response[KEYS['RESPONSE_KEYS']['BASIC']]:
        raise EmptyFieldException()
    logger.debug('Ответ от API успешно проверен.')
    return response[KEYS['RESPONSE_KEYS']['BASIC']]


def make_work_values(work) -> list:
    """Подготавливаем данные для записи в БД."""
    work_values = []
    for field in DB_FIELDS['WRITE']:
        work_values.append(0)
        if field in work:
            work_values[-1] = work[field]
    logger.debug('Данные для записи в БД подготовлены.')
    return work_values


def get_works_from_db(session) -> dict:
    """Получаем данные о работах из БД."""
    result_sets = session.transaction(ydb.SerializableReadWrite()).execute(
        """
        PRAGMA TablePathPrefix("{}");
        SELECT {}, {} FROM {};
        """.format(
            ENDPOINTS['YDB_DATABASE'],
            *DB_FIELDS['READ'],
            DB_FIELDS['TABLE']
        ),
        commit_tx=True,
    )
    parse = {}
    for work in result_sets[0].rows:
        parse[
            work[KEYS['PARSE_KEYS']['OTHER']]
        ] = work[KEYS['PARSE_KEYS']['BASIC']]
    logger.debug('Данные из БД получены.')
    return parse


def write_work_in_db(pool, work_values) -> None:
    """Записываем данные о работе в БД."""
    def calldb(session):
        session.transaction().execute(
            """
            PRAGMA TablePathPrefix("{}");
            UPSERT INTO {} ({}, {}, {}, {}, {}, {})
            VALUES ({}, "{}", "{}", "{}", "{}", "{}");
            """.format(
                ENDPOINTS['YDB_DATABASE'],
                DB_FIELDS['TABLE'],
                *DB_FIELDS['WRITE'],
                *work_values
            ),
            commit_tx=True,
        )
        logger.debug('Данные в БД успешно записаны.')
    return pool.retry_operation_sync(calldb)


def write_message(work) -> str:
    """Формируем сообщение для отправки."""
    message = []
    for key, value in KEYS['MESSAGE_KEYS'].items():
        if key in work and work[key]:
            if not isinstance(value, dict):
                text = f'{value} {work[key]}.'
            elif work[key] in value:
                text = str(value[work[key]])
            else:
                text = f'Отсутствует значение у ключа {key}: {work[key]}.'
                logger.error(text)
            message.append(text)
    logger.debug('Сообщение о изменении статуса успешно подготовлено.')
    return ' '.join(message)


def check_work(work, saved_works) -> bool:
    """Проверяем изменился ли статус работы."""
    for field in KEYS['PARSE_KEYS'].values():
        if field not in work:
            raise FieldException(field)
    logger.debug('В словаре есть требуемые ключи')
    status = work[KEYS['PARSE_KEYS']['BASIC']]
    hw_name = work[KEYS['PARSE_KEYS']['OTHER']]
    if hw_name in saved_works and status == saved_works[hw_name]:
        logger.info(f'Статус домашней работы "{hw_name}" не изменился')
        return False
    else:
        logger.info(
            f'Статус домашней работы "{hw_name}" изменился на "{status}"'
        )
        return True


def check_tokens() -> bool:
    """Проверяем доступность переменных окружения."""
    check = True
    for key, value in TOKENS.items(), ENDPOINTS.items():
        if not value:
            check = False
            logger.critical(CriticalException(key))
    return check


def main(event, context):
    """Основная логика работы бота."""
    if not check_tokens:
        logger.critical('Программа принудительно остановлена.')
        sys.exit()
    bot = telegram.Bot(token=TOKENS['TELEGRAM_TOKEN'])
    try:
        old_message = read_s3(S3_FIELDS['MESSAGE'])
        response = get_api_answer(KEYS['TIMESTAMP'])
        homeworks = check_response(response)
        saved_works = pool.retry_operation_sync(get_works_from_db)
        for work in homeworks:
            if check_work(work, saved_works):
                write_work_in_db(pool, make_work_values(work))
                send_message(bot, write_message(work))
    except Exception as error:
        message = f'Сбой в работе программы: {error}'
        logger.error(message)
        if old_message != message:
            send_message(bot, message)
            write_s3(S3_FIELDS['MESSAGE'], message)
    return {
        'statusCode': 200,
        'body': 'its alive',
    }
