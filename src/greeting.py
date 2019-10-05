import logging
from typing import Dict, Any

from telebot.types import InlineKeyboardButton, User, InlineKeyboardMarkup, Message

from dto import GreetingQuestionDto, NewbieDto
from error import UserAlreadyInStorageError, UserNotFoundInStorageError, UserStorageUpdateError


class NewbieStorage:
    _storage: Dict[Any, NewbieDto]

    def __init__(self, logger: logging.Logger):
        self._storage = dict()
        self._logger = logger

    def __iter__(self):
        for key, value in self._storage.items():
            yield value

    def add(self, user: User, timeout: int, question: GreetingQuestionDto):
        newbie = NewbieDto(user=user, timeout=timeout, question=question)
        self._logger.debug(f'Trying to add user @{user.username} into newbie list')
        if user.id in self._storage:
            self._logger.warning(f'Can not add! User @{user.username} already in newbie list.')
            raise UserAlreadyInStorageError()

        self._storage.update({user.id: newbie})

    def remove(self, user: User):
        try:
            self._logger.debug(f'Trying to remove newbie {user} from list')
            del self._storage[user.id]
        except KeyError:
            self._logger.warning(f'Can not remove! User @{user.username} not found in newbie list!')

    def update(self, user: User, greeting: Message):
        self._logger.debug(f'Trying to update greeting {greeting} for newbie @{user.username}')
        try:
            current_newbie = self.get(user)
        except UserNotFoundInStorageError:
            raise UserStorageUpdateError()
        self._storage[user.id] = NewbieDto(
            user=current_newbie.user,
            timeout=current_newbie.timeout,
            question=current_newbie.question,
            greeting=greeting,
        )

    def get(self, user: User) -> NewbieDto:
        try:
            return self._storage[user.id]
        except KeyError:
            self._logger.error(f'Can not get! User @{user.username} not found in newbie list.')
            raise UserNotFoundInStorageError()

    def get_user_list(self) -> list:
        return list(self._storage.keys())


class QuestionProvider:
    @staticmethod
    def get_question() -> GreetingQuestionDto:
        return GreetingQuestionDto(
            text='{mention}, прочитал(а) правила чата?',
            keyboard=InlineKeyboardMarkup().row(
                InlineKeyboardButton(text='Да, принял(а) к сведению.', callback_data='да'),
                InlineKeyboardButton(text='Нет, но сейчас прочитаю.', callback_data='нет'),
            ),
            timeout=120,
            reply={
                'да': '*{first_name} считает, что да.*',
                'нет': '*{first_name} считает, что нет. ¯\\_(ツ)_/¯*',
            }

        )
