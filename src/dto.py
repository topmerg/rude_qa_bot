from typing import Dict

from telebot.types import ReplyKeyboardMarkup, User, Message


class DurationDto:
    _seconds: int
    _text: str

    def __init__(self, seconds: int, text: str):
        self._seconds = seconds
        self._text = text

    @property
    def seconds(self) -> int:
        return self._seconds

    @property
    def text(self) -> str:
        return self._text


class PluralFormsDto:
    _form_1: str
    _form_2: str
    _form_3: str

    def __init__(self, form_1: str, form_2: str, form_3: str):
        self._form_1 = form_1
        self._form_2 = form_2
        self._form_3 = form_3

    @property
    def form_1(self) -> str:
        return self._form_1

    @property
    def form_2(self) -> str:
        return self._form_2

    @property
    def form_3(self) -> str:
        return self._form_3


class GreetingQuestionDto:
    _text: str
    _keyboard: ReplyKeyboardMarkup
    _timeout: int
    _reply: Dict[str, str]

    def __init__(self, text: str, keyboard: ReplyKeyboardMarkup, timeout: int, reply: Dict[str, str]):
        self._text = text
        self._keyboard = keyboard
        self._timeout = timeout
        self._reply = reply

    @property
    def text(self) -> str:
        return self._text

    @property
    def keyboard(self) -> ReplyKeyboardMarkup:
        return self._keyboard

    @property
    def timeout(self) -> int:
        return self._timeout

    @property
    def reply(self) -> Dict[str, str]:
        return self._reply


class NewbieDto:
    _user: User
    _timeout: int
    _question: GreetingQuestionDto
    _greeting: Message

    def __init__(self, user: User, timeout: int, question: GreetingQuestionDto, greeting: Message = None):
        self._user = user
        self._timeout = timeout
        self._question = question
        self._greeting = greeting

    @property
    def user(self) -> User:
        return self._user

    @property
    def timeout(self) -> int:
        return self._timeout

    @property
    def question(self) -> GreetingQuestionDto:
        return self._question

    @property
    def greeting(self) -> Message:
        return self._greeting
