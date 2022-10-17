class CriticalException(Exception):
    """Критическое исключение отсутствия переменной окружения."""

    def __init__(self, variable: str) -> None:
        self.variable = variable

    def __str__(self) -> str:
        return (
            f'Отсутствует обязательная переменная окружения: {self.variable}'
        )


class ResponseCodeException(Exception):
    """Исключение неправильного кода ответа эндпоинта."""

    def __init__(self, code: int, endpoint: str) -> None:
        self.code = code
        self.endpoint = endpoint

    def __str__(self) -> str:
        if self.code == 404:
            return (
                f'Эндпоинт: {self.endpoint} недоступен. '
                f'Код ответа API: {self.code}'
            )
        else:
            return (
                f'Эндпоинт: {self.endpoint} ответил с кодом: {self.code}'
            )


class FieldTypeException(TypeError):
    """Исключение неправильного формата ответа эндпоинта."""

    def __init__(self, expectedformat: str, responseformat: str) -> None:
        self.expectedformat = expectedformat
        self.responseformat = responseformat

    def __str__(self) -> str:
        return (
            f'Неправильный формат ответа эндпоинта, должен быть '
            f'{self.expectedformat} а пришел: {self.responseformat}'
        )


class FieldException(KeyError):
    """Исключение при неправильном содержании ответа."""

    def __init__(self, responseitem: str) -> None:
        self.responseitem = responseitem

    def __str__(self) -> str:
        return (
            f'В ответе отсутствую обязательные '
            f'поля: {self.responseitem}'
        )


class EmptyFieldException(Exception):
    """Исключение пустого поля ответа эндпоинта."""

    def __str__(self) -> str:
        return (
            'Список работ пуст'
        )


class SendMessageException(Exception):
    """Исключение при ошибках отправки сообщения в чат."""

    def __init__(self, telegramerror: str) -> None:
        self.telegramerror = telegramerror

    def __str__(self) -> str:
        return (
            f'При отправке сообщения возникла ошибка: {self.telegramerror}'
        )


class SendRequestException(Exception):
    """Исключение при ошибках отправки запроса к эндпоинту."""

    def __init__(self, requesterror: str) -> None:
        self.requesterror = requesterror

    def __str__(self) -> str:
        return (
            f'При запросе к эндпоинту возникла ошибка: {self.requesterror}'
        )
