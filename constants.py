"""Константы."""

import os

KEYS = {
    'TIMESTAMP': 0,
    'RESPONSE_KEYS': {
        'BASIC': 'homeworks',
        'OTHER': 'current_date',
    },
    'PARSE_KEYS': {
        'BASIC': 'status',
        'OTHER': 'homework_name',
    },
    'MESSAGE_KEYS': {
        'lesson_name': 'Изменился статус проверки работы -',
        'status': {
            'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
            'reviewing': 'Работа взята на проверку ревьюером.',
            'rejected': 'Работа проверена: у ревьюера есть замечания.'
        },
        'reviewer_comment': 'Комментарий ревьюера:',
    },
}

TOKENS = {
    'PRACTICUM_TOKEN': os.getenv('PRACTICUM_TOKEN'),
    'TELEGRAM_TOKEN': os.getenv('TELEGRAM_TOKEN'),
    'TELEGRAM_CHAT_ID': os.getenv('TELEGRAM_CHAT_ID'),
    'AWS_ACCESS_KEY_ID': os.getenv('AWS_ACCESS_KEY_ID'),
    'AWS_SECRET_ACCESS_KEY': os.getenv('AWS_SECRET_ACCESS_KEY'),
}

HEADERS = {'Authorization': f'OAuth {TOKENS["PRACTICUM_TOKEN"]}'}

ENDPOINTS = {
    'YP_ENDPOINT': os.getenv('YP_ENDPOINT'),
    'S3_ENDPOINT': os.getenv('S3_ENDPOINT'),
    'YDB_ENDPOINT': os.getenv('YDB_ENDPOINT'),
    'YDB_DATABASE': os.getenv('YDB_DATABASE'),
}


DB_FIELDS = {
    'WRITE': [
        'id',
        KEYS['PARSE_KEYS']['BASIC'],
        KEYS['PARSE_KEYS']['OTHER'],
        'reviewer_comment',
        'date_updated',
        'lesson_name'
    ],
    'READ': [
        KEYS['PARSE_KEYS']['BASIC'],
        KEYS['PARSE_KEYS']['OTHER'],
    ],
    'TABLE': 'works'
}

S3_FIELDS = {
    'BUCKET': 'test-bot',
    'MESSAGE': 'message',
    'RESPONSE': 'response'
}
