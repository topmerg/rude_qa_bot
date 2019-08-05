import logging
from typing import Dict, Any

from telebot.types import User

from dto import RestrictedUserDto
from error import UserNotFoundInStorageError


class RestrictionStorage:
    _storage: Dict[Any, RestrictedUserDto]

    def __init__(self, logger: logging.Logger):
        self._storage = dict()
        self._logger = logger

    def add(self, restricted: RestrictedUserDto):
        self._logger.debug(f'Trying to add user @{restricted.user.username} into restricted users list')
        self._storage.update({restricted.user.id: restricted})

    def get(self, user: User) -> RestrictedUserDto:
        try:
            return self._storage[user.id]
        except KeyError:
            self._logger.error(f'Can not get! User @{user.username} not found in restricted users list.')
            raise UserNotFoundInStorageError()
