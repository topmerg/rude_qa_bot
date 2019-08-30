import logging
import threading
import time

from telebot import TeleBot
from telebot.apihelper import ApiException
from telebot.types import User, Message

from const import RestrictDuration, TelegramParseMode, ChatCommand, BanDuration, TelegramChatType, PunishmentDuration, \
    BaseDuration
from dto import DurationDto, PluralFormsDto, RestrictedUserDto, NewbieDto, RestrictionDto
from error import ParseBanDurationError, InvalidConditionError, UserNotFoundInStorageError
from greeting import NewbieStorage
from notification import Notification
from restriction import RestrictionStorage


class BotUtils:
    _bot: TeleBot
    _chat_id: int
    _notification: Notification
    _newbie_storage: NewbieStorage
    _restriction_storage: RestrictionStorage
    _logger: logging.Logger

    def __init__(
            self,
            bot: TeleBot,
            chat_id: str,
            notification: Notification,
            newbie_storage: NewbieStorage,
            restriction_storage: RestrictionStorage,
            logger: logging.Logger,
    ):
        self._bot = bot
        self._chat_id = int(chat_id)
        self._notification = notification
        self._newbie_storage = newbie_storage
        self._restriction_storage = restriction_storage
        self._logger = logger

    @property
    def chat_id(self) -> int:
        return self._chat_id

    @staticmethod
    def prepare_query(text: str) -> str:
        """
        Get text without command

        example: prepare_query("/getUser rudeboy from rude qa") -> returns "rudeboy from rude qa"
        """
        return ' '.join(text.split()[1:])

    def get_duration(self, text: str, duration_class: BaseDuration) -> DurationDto:
        if text == '':
            return self.get_duration(f'{duration_class.DEFAULT_DURATION}{duration_class.DEFAULT_UNIT}', duration_class)

        try:
            amount = int(text)
            return self.get_duration(f'{amount}{duration_class.DEFAULT_UNIT}', duration_class)
        except ValueError:
            pass

        try:
            amount = int(text[:-1])
            unit = duration_class.UNITS[text[-1]]

            duration_seconds = int(amount * unit['rate'])

            if duration_seconds < duration_class.MIN_DURATION.seconds:
                return duration_class.MIN_DURATION

            if duration_seconds > duration_class.MAX_DURATION.seconds:
                return duration_class.MAX_DURATION

            duration_unit = self.get_plural(amount, unit['plural_forms'])

            return DurationDto(
                seconds=duration_seconds,
                text=f'{amount} {duration_unit}',
            )
        except (ValueError, KeyError, IndexError):
            raise ParseBanDurationError

    @staticmethod
    def get_plural(amount: int, plural_forms: PluralFormsDto) -> str:
        if amount % 10 == 1 and amount % 100 != 11:
            return plural_forms.form_1

        if 2 <= amount % 10 <= 4 and (amount % 100 < 10 or amount % 100 >= 20):
            return plural_forms.form_2

        return plural_forms.form_3

    @staticmethod
    def mention(user: User):
        return f'[{user.first_name}](tg://user?id={user.id})'

    def delete_chat_message(self, message: Message):
        try:
            self._bot.delete_message(message.chat.id, message.message_id)
        except ApiException:
            self._logger.error(f'Can not delete chat message {message}')

    def remove_inline_keyboard(self, message: Message):
        try:
            self._logger.debug(f'Trying to edit {message}')
            self._bot.edit_message_text(
                message.html_text,
                chat_id=message.chat.id,
                message_id=message.message_id,
                parse_mode=TelegramParseMode.HTML,
            )
        except ApiException:
            self._logger.error(f'Can not edit chat message {message}')

    def check_current_restrictions(self, user: User, message: Message, duration: DurationDto, command: str):
        chat_member = self._bot.get_chat_member(message.chat.id, user.id)

        restriction_list = {
            ChatCommand.RO: RestrictionDto(
                True,
                True if chat_member.can_send_media_messages is None else chat_member.can_send_media_messages,
                True if chat_member.can_send_other_messages is None else chat_member.can_send_other_messages,
                True if chat_member.can_add_web_page_previews is None else chat_member.can_add_web_page_previews,
            ),
            ChatCommand.TO: RestrictionDto(
                True,
                True,
                True if chat_member.can_send_other_messages is None else chat_member.can_send_other_messages,
                True if chat_member.can_add_web_page_previews is None else chat_member.can_add_web_page_previews,
            ),
        }

        restricted_user = RestrictedUserDto(
            user=user,
            chat_id=message.chat.id,
            until_date=0 if chat_member.until_date is None else chat_member.until_date,
            restriction=restriction_list.get(command, RestrictionDto(True, True, True, True)),
            restore_at=message.date + duration.seconds,
        )

        self._restriction_storage.add(restricted_user)
        if not restricted_user.until_date or restricted_user.until_date > message.date + duration.seconds:
            self.create_scheduled_threat(duration.seconds, self.restore_restriction, (restricted_user,))

    def set_read_only(self, user: User, message: Message, duration: DurationDto) -> str:
        self.check_current_restrictions(
            user=user,
            message=message,
            duration=duration,
            command=ChatCommand.RO,
        )

        self._bot.restrict_chat_member(
            chat_id=message.chat.id,
            user_id=user.id,
            until_date=message.date + duration.seconds,
            can_send_messages=False,
        )
        restriction_text = self._notification.read_only(
            first_name=user.first_name,
            duration_text=duration.text,
        )

        return restriction_text

    def set_text_only(self, user: User, message: Message, duration: DurationDto) -> str:
        self.check_current_restrictions(
            user=user,
            message=message,
            duration=duration,
            command=ChatCommand.TO,
        )

        self._bot.restrict_chat_member(
            chat_id=message.chat.id,
            user_id=user.id,
            until_date=message.date + duration.seconds,
            can_send_messages=True,
            can_send_media_messages=False,
        )
        restriction_text = self._notification.text_only(
            first_name=user.first_name,
            duration_text=duration.text,
        )

        return restriction_text

    def set_punishment(self, user: User, message: Message) -> str:
        duration = PunishmentDuration.DURATION
        self.set_read_only(
            user=user,
            message=message,
            duration=duration
        )

        restriction_text = self._notification.unauthorized_punishment(
            first_name=user.first_name,
        )

        return restriction_text

    def set_read_write(self, user: User, message: Message) -> str:
        self._bot.restrict_chat_member(
            chat_id=message.chat.id,
            user_id=user.id,
            can_send_messages=True,
            can_send_media_messages=True,
            can_send_other_messages=True,
            can_add_web_page_previews=True,
        )
        restriction_text = self._notification.read_write(first_name=user.first_name)

        return restriction_text

    def ban_kick(self, user: User, message: Message, duration: DurationDto) -> str:
        self._newbie_storage.remove(user)

        self._bot.kick_chat_member(
            chat_id=message.chat.id,
            user_id=user.id,
            until_date=message.date + duration.seconds,
        )
        self._logger.info(f'@{user.username} was banned by {message.from_user.username} for {duration.text}.')

        duration_text = duration.text
        if duration.seconds > 0:
            duration_text = f'на {duration.text}'

        kick_text = self._notification.ban_kick(user.first_name, duration_text)

        return kick_text

    def create_scheduled_threat(self, pause: int, action, args: tuple):
        threading.Thread(target=self._handle_scheduled_task, args=(pause, action, args,)).start()

    @staticmethod
    def _handle_scheduled_task(pause: int, action, args: tuple):
        time.sleep(pause)
        action(*args)

    def timeout_kick(self, newbie: NewbieDto):
        greeting_message = newbie.greeting
        user = newbie.user
        if user.id not in self._newbie_storage.get_user_list():
            return

        self._newbie_storage.remove(user)
        self.remove_inline_keyboard(greeting_message)

        kick_text = self._notification.timeout_kick(user.first_name)
        kick_message = self._bot.send_message(
            chat_id=greeting_message.chat.id,
            text=f'*{kick_text}*',
            reply_to_message_id=greeting_message.message_id,
            parse_mode=TelegramParseMode.MARKDOWN
        )
        try:
            self._bot.kick_chat_member(
                chat_id=greeting_message.chat.id,
                user_id=user.id,
                until_date=kick_message.date + BanDuration.AUTO_KICK_DURATION_SECONDS,
            )
            self._logger.info(f'@{user.username} was kicked from chat due greeting timeout.')
        except ApiException:
            self._logger.error(f'Can not kick chat member @{user.username}')
            self.delete_chat_message(kick_message)

    def restore_restriction(self, restricted: RestrictedUserDto):
        try:
            try:
                actual_restricted = self._restriction_storage.get(restricted.user)
            except UserNotFoundInStorageError:
                raise InvalidConditionError()

            if actual_restricted.restore_at != restricted.restore_at:
                raise InvalidConditionError()

            self._bot.restrict_chat_member(
                chat_id=restricted.chat_id,
                user_id=restricted.user.id,
                until_date=max(
                    restricted.until_date,
                    time.time() + RestrictDuration.UNSAFE_DURATION_SECONDS
                ),
                can_send_messages=restricted.restriction.messages,
                can_send_media_messages=restricted.restriction.media,
                can_send_other_messages=restricted.restriction.other,
                can_add_web_page_previews=restricted.restriction.web_preview,
            )
            self._logger.info(
                f'Custom restriction was restored for @{restricted.user.username}. {restricted.restriction.__dict__}'
            )
        except ApiException:
            self._logger.error(f'Can not set custom restriction for chat member @{restricted.user.username}')
        except InvalidConditionError:
            pass

    def rude_qa_only(self, handler):
        def wrapper(message: Message):
            if message.chat.id == self.chat_id:
                return handler(message)

        return wrapper

    @staticmethod
    def supergroup_only(handler):
        def wrapper(message: Message):
            try:
                if message.chat.type == TelegramChatType.SUPER_GROUP:
                    return handler(message)
            except TypeError:
                pass

        return wrapper
