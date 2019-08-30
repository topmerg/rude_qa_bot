import logging

import telebot
from telebot.types import Message

from const import TelegramParseMode


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
    def __init__(self, message: Message, service, bot: telebot, logger: logging.Logger):
        text = service.set_punishment(user=message.from_user, message=message)
        logger.warning(f'Non-factor {message.from_user.username} trying to use unauthorized command.')
        bot.send_message(
            chat_id=message.chat.id,
            text=f'*{text}*',
            reply_to_message_id=message.message_id,
            parse_mode=TelegramParseMode.MARKDOWN,
        )
