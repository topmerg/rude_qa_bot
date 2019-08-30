import logging

from telebot.types import Message


class ParseBanDurationError(Exception):
    pass


class InvalidCommandError(Exception):
    pass


class InvalidConditionError(Exception):
    pass


class UserAlreadyInStorageError(Exception):
    pass


class UserNotFoundInStorageError(Exception):
    pass


class UserStorageUpdateError(Exception):
    pass


class UnauthorizedCommandError(InvalidConditionError):
    def __init__(self, message: Message, service, logger: logging.Logger):
        service.set_punishment(user=message.from_user, message=message)
        logger.warning(f'Non-factor {message.from_user.username} trying to use unauthorized command.')
