import copy
import logging
from typing import Dict, Any

from telebot.types import InlineKeyboardButton, User, InlineKeyboardMarkup, Message

from dto import GreetingQuestionDto, NewbieDto
from error import NewbieAlreadyInStorageError, NewbieNotFoundInStorageError, NewbieStorageUpdateError


class NewbieStorage:
    _storage: Dict[Any, NewbieDto]

    def __init__(self, logger: logging.Logger):
        self._storage = dict()
        self._logger = logger

    def add(self, user: User, timeout: int, question: GreetingQuestionDto):
        newbie = NewbieDto(user=user, timeout=timeout, question=question)
        self._logger.debug(f'Trying to add user @{user.username} into newbie list')
        if user.id in self._storage:
            self._logger.warning(f'Can not add! User @{user.username} already in newbie list.')
            raise NewbieAlreadyInStorageError()

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
        except NewbieNotFoundInStorageError:
            raise NewbieStorageUpdateError()
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
            raise NewbieNotFoundInStorageError()

    def get_user_list(self) -> list:
        return list(self._storage.keys())

    def get_expired(self, now: int):
        newbie_list = copy.deepcopy(self._storage).values()
        for newbie in newbie_list:
            if newbie.timeout < now:
                yield newbie


class QuestionProvider:
    @staticmethod
    def get_question() -> GreetingQuestionDto:
        return GreetingQuestionDto(
            text='{mention}, UI это API?',
            keyboard=InlineKeyboardMarkup().row(
                InlineKeyboardButton(text='Да, определённо!', callback_data='да'),
                InlineKeyboardButton(text='Нет, обоссыте меня', callback_data='нет'),
            ),
            timeout=120,
            reply={
                'да': '*{first_name} считает, что да.*',
                'нет': '*{first_name} считает, что нет. ¯\_(ツ)_/¯*',
            }

        )
