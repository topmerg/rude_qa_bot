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


class RestrictionDto:
    _messages: bool
    _media: bool
    _other: bool
    _web_preview: bool

    def __init__(self, messages: bool, media: bool, other: bool, web_preview: bool):
        self._messages = messages
        self._media = media
        self._other = other
        self._web_preview = web_preview

    @property
    def messages(self) -> bool:
        return self._messages

    @property
    def media(self) -> bool:
        return self._media

    @property
    def other(self) -> bool:
        return self._other

    @property
    def web_preview(self) -> bool:
        return self._web_preview


class RestrictedUserDto:
    _user: User
    _chat_id: int
    _until_date: int
    _restriction: RestrictionDto
    _restore_at: int

    def __init__(self, user: User, chat_id: int, until_date: int, restriction: RestrictionDto, restore_at: int):
        self._user = user
        self._chat_id = chat_id
        self._until_date = until_date
        self._restriction = restriction
        self._restore_at = restore_at

    @property
    def user(self) -> User:
        return self._user

    @property
    def chat_id(self) -> int:
        return self._chat_id

    @property
    def until_date(self) -> int:
        return self._until_date

    @property
    def restriction(self) -> RestrictionDto:
        return self._restriction

    @property
    def restore_at(self) -> int:
        return self._restore_at
