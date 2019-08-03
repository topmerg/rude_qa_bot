import logging
import threading
import time

from telebot import TeleBot
from telebot.apihelper import ApiException
from telebot.types import Message, CallbackQuery, User

from const import TelegramChatType, EnvVar, TelegramParseMode, LoggingSettings, RestrictCommand, \
    RestrictDuration, BanDuration
from dto import NewbieDto, DurationDto, RestrictionDto, RestrictedUserDto
from env_loader import EnvLoader
from error import ParseBanDurationError, UserAlreadyInStorageError, UserStorageUpdateError, \
    InvalidCommandError, InvalidConditionError, UserNotFoundInStorageError
from greeting import QuestionProvider, NewbieStorage
from notification import Notification
from utils import BotUtils

logging.basicConfig(
    format=LoggingSettings.RECORD_FORMAT,
    datefmt=LoggingSettings.DATE_FORMAT,
    level=logging.getLevelName(logging.DEBUG)
)
logger = logging.getLogger()
env_loader = EnvLoader(logger)
env_loader.from_file()
logger.setLevel(env_loader.get(EnvVar.LOGGING_LEVEL, LoggingSettings.DEFAULT_LEVEL))

bot = TeleBot(
    token=env_loader.get_required(EnvVar.TELEGRAM_TOKEN, sensitive=True),
    skip_pending=True
)

newbie_storage = NewbieStorage(logger)
methods = BotUtils(env_loader.get_required(EnvVar.TELEGRAM_CHAT_ID))
notification = Notification()


def rude_qa_only(handler):
    def wrapper(message: Message):
        if message.chat.id == methods.chat_id:
            return handler(message)

    return wrapper


def supergroup_only(handler):
    def wrapper(message: Message):
        try:
            if message.chat.type == TelegramChatType.SUPER_GROUP:
                return handler(message)
        except TypeError:
            pass

    return wrapper


@bot.message_handler(func=lambda m: m.text == 'ping')
@supergroup_only
@rude_qa_only
def ping_handler(message: Message):
    bot.send_message(message.chat.id, 'pong')


@bot.message_handler(commands=['me'])
@rude_qa_only
@supergroup_only
def me_irc(message: Message):
    try:
        query = methods.prepare_query(message.text)

        if query:
            bot.delete_message(message.chat.id, message.message_id)
            bot.send_message(message.chat.id, '*{}* _{}_'.format(message.from_user.first_name, query),
                             parse_mode=TelegramParseMode.MARKDOWN)
        else:
            bot.delete_message(message.chat.id, message.message_id)
    except (ApiException, IndexError):
        bot.send_message(
            message.chat.id, 'Братиш, наебнулось. Посмотри логи.')


@bot.message_handler(func=lambda m: m.text and m.text[:4].rstrip() in [
    RestrictCommand.RO,
    RestrictCommand.TO
])
@rude_qa_only
@supergroup_only
def restrict_handler(message: Message):
    try:
        if message.forward_from:
            raise InvalidConditionError()

        command = message.text[:3]
        task_list = {
            f'{RestrictCommand.RO}': set_read_only,
            f'{RestrictCommand.TO}': set_text_only,
        }

        admin_list = [x.user.id for x in bot.get_chat_administrators(message.chat.id)]
        if message.from_user.id in admin_list:
            try:
                target_message = message.reply_to_message
                if target_message.from_user.id in admin_list:
                    logger.warning(f'@{message.from_user.username} trying to restrict another admin. Abort.')
                    raise InvalidConditionError()
            except AttributeError:
                raise InvalidConditionError()
        else:
            logger.warning(f'Non-factor {message.from_user.username} trying to use restrict command. Reflect!')
            target_message = message
            command = RestrictCommand.RO

        try:
            query = methods.prepare_query(message.text)
            restrict_duration = methods.get_duration(query)
        except ParseBanDurationError:
            raise InvalidCommandError

        target_user = target_message.from_user
        try:
            logger.info(f'Try to use restrict @{target_user.username} for {query}.')
            check_current_restrictions(target_user, message, restrict_duration, command)
            try:
                restrict_task = task_list.get(command)
                ban_text = restrict_task(
                    user=target_user,
                    message=message,
                    duration=restrict_duration
                )
            except (KeyError, TypeError):
                raise InvalidCommandError()

            bot.send_message(message.chat.id, f'*{ban_text}*', parse_mode=TelegramParseMode.MARKDOWN)
        except ApiException:
            logger.error(f'Can not restrict chat member {target_user}')

    except InvalidCommandError:
        logger.warning(f'Can not execute command \'{message.text}\' from @{message.from_user.username}')
        try:
            bot.delete_message(message.chat.id, message.message_id)
        except ApiException:
            logger.error(f'Can not delete chat message {message}')
    except InvalidConditionError:
        pass


def check_current_restrictions(user: User, message: Message, duration: DurationDto, command: str):
    chat_member = bot.get_chat_member(message.chat.id, user.id)

    if command == RestrictCommand.RO:
        restriction = RestrictionDto(
            chat_member.can_send_messages,
            chat_member.can_send_media_messages,
            chat_member.can_send_other_messages,
            chat_member.can_add_web_page_previews,
        )
    else:
        restriction = RestrictionDto(True, True, True, True)

    restricted_user = RestrictedUserDto(
        user=user,
        chat_id=message.chat.id,
        until_date=0 if chat_member.until_date is None else chat_member.until_date,
        restriction=restriction,
    )

    create_scheduled_threat(duration.seconds, set_restriction, (restricted_user,))


def set_read_only(user: User, message: Message, duration: DurationDto) -> str:
    bot.restrict_chat_member(
        chat_id=message.chat.id,
        user_id=user.id,
        until_date=message.date + duration.seconds,
    )
    ban_text = notification.read_only(
        first_name=user.first_name,
        duration_text=duration.text,
    )

    return ban_text


def set_text_only(user: User, message: Message, duration: DurationDto) -> str:
    bot.restrict_chat_member(
        chat_id=message.chat.id,
        user_id=user.id,
        until_date=message.date + duration.seconds,
        can_send_messages=True,
    )
    ban_text = notification.text_only(
        first_name=user.first_name,
        duration_text=duration.text,
    )

    return ban_text


@bot.message_handler(content_types=['new_chat_members'])
@rude_qa_only
def greeting_handler(message: Message):
    for new_user in message.new_chat_members:
        logger.info(f'New member joined the group: {new_user}')
        question = QuestionProvider.get_question()

        try:
            newbie_storage.add(user=new_user, timeout=message.date + question.timeout, question=question)
        except UserAlreadyInStorageError:
            return timeout_kick(newbie_storage.get(new_user))

        logger.info(f'Trying to temporary restrict all users content for @{new_user.username}')
        try:
            bot.restrict_chat_member(
                chat_id=message.chat.id,
                user_id=new_user.id,
                until_date=message.date + question.timeout * 2,
            )
        except ApiException:
            logger.error(f'Can not restrict chat member {new_user}')
            return

        greeting_message = bot.send_message(
            chat_id=message.chat.id,
            text=question.text.format(mention=methods.mention(new_user)),
            reply_markup=question.keyboard,
            reply_to_message_id=message.message_id,
            parse_mode=TelegramParseMode.MARKDOWN,
        )
        try:
            newbie_storage.update(
                user=new_user,
                greeting=greeting_message
            )
            create_scheduled_threat(question.timeout, timeout_kick, (newbie_storage.get(new_user),))
        except (UserStorageUpdateError, UserNotFoundInStorageError):
            try:
                bot.delete_message(message.chat.id, greeting_message.message_id)
            except ApiException:
                logger.error(f'Can not delete chat message {message}')


@bot.callback_query_handler(func=lambda call: True)
def greeting_callback(call: CallbackQuery):
    if call.message and call.from_user.id in newbie_storage.get_user_list():
        remove_inline_keyboard(call.message)
        try:
            reply = newbie_storage.get(call.from_user).question.reply[call.data]
        except (KeyError, TypeError):
            reply = '*{first_name} ответил "{call_data}".*'
        bot.send_message(
            chat_id=call.message.chat.id,
            text=reply.format(first_name=call.from_user.first_name, call_data=call.data),
            reply_to_message_id=call.message.message_id,
            parse_mode=TelegramParseMode.MARKDOWN,

        )

        newbie_storage.remove(call.from_user)
        try:
            bot.restrict_chat_member(
                chat_id=call.message.chat.id,
                user_id=call.from_user.id,
                can_send_messages=True,
            )
        except ApiException:
            logger.error(f'Can not disable restriction for chat member @{call.from_user.username}')


def remove_inline_keyboard(greeting_message: Message):
    try:
        logger.debug(f'Trying to edit {greeting_message}')
        bot.edit_message_text(
            greeting_message.html_text,
            chat_id=greeting_message.chat.id,
            message_id=greeting_message.message_id,
            parse_mode=TelegramParseMode.HTML,
        )
    except ApiException:
        logger.error(f'Can not edit chat message {greeting_message}')


def timeout_kick(newbie: NewbieDto):
    greeting_message = newbie.greeting
    user = newbie.user
    newbie_storage.remove(user)
    remove_inline_keyboard(greeting_message)
    kick_text = notification.timeout_kick(user.first_name)
    kick_message = bot.send_message(
        chat_id=greeting_message.chat.id,
        text=f'*{kick_text}*',
        reply_to_message_id=greeting_message.message_id,
        parse_mode=TelegramParseMode.MARKDOWN
    )
    try:
        bot.kick_chat_member(
            chat_id=greeting_message.chat.id,
            user_id=user.id,
            until_date=kick_message.date + BanDuration.DURATION_SECONDS,
        )
        logger.info(f'@{user.username} was kicked from chat due greeting timeout.')
    except ApiException:
        logger.error(f'Can not kick chat member @{user.username}')
        try:
            bot.delete_message(kick_message.chat.id, kick_message.message_id)
        except ApiException:
            logger.error(f'Can not delete chat message {kick_message}')


def set_restriction(restricted: RestrictedUserDto):
    try:
        if (restricted.restriction.messages in [None, True]) and \
                (restricted.restriction.media in [None, True]) and \
                (restricted.restriction.other in [None, True]) \
                and (restricted.restriction.web_preview in [None, True]):
            bot.promote_chat_member(
                chat_id=restricted.chat_id,
                user_id=restricted.user.id,
            )
        else:
            bot.restrict_chat_member(
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
        logger.info(f'Custom restriction was restored for @{restricted.user.username}.')
    except ApiException:
        logger.error(f'Can not set custom restriction for chat member @{restricted.user.username}')


def create_scheduled_threat(pause: int, action, args: tuple):
    threading.Thread(target=handle_scheduled_task, args=(pause, action, args,)).start()


def handle_scheduled_task(pause: int, action, args: tuple):
    time.sleep(pause)
    action(*args)


if __name__ == '__main__':
    bot.polling()
