from restriction import RestrictionStorage

__version__ = '1.0.12'

import logging

from telebot import TeleBot
from telebot.apihelper import ApiException
from telebot.types import Message, CallbackQuery

from const import EnvVar, TelegramParseMode, LoggingSettings, ChatCommand, \
    MessageSettings, BanDuration, RestrictDuration, TelegramMemberStatus
from env_loader import EnvLoader
from error import ParseBanDurationError, UserAlreadyInStorageError, UserStorageUpdateError, \
    InvalidCommandError, InvalidConditionError, UserNotFoundInStorageError, UnauthorizedCommandError
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
restriction_storage = RestrictionStorage(logger)
notification = Notification()
methods = BotUtils(
    bot,
    env_loader.get_required(EnvVar.TELEGRAM_CHAT_ID),
    notification,
    newbie_storage,
    restriction_storage,
    logger
)


@bot.message_handler(commands=['ping', 'id', 'ver'])
@methods.rude_qa_only
@methods.supergroup_only
def test_handler(message: Message):
    response_list = {
        '/ping': 'pong',
        '/id': message.chat.id,
        '/ver': __version__,
    }

    try:
        admin_list = [x.user.id for x in bot.get_chat_administrators(message.chat.id)]
        if message.from_user.id not in admin_list:
            raise InvalidConditionError()

        response_message = bot.send_message(message.chat.id, response_list[message.text])
        for current_message in message, response_message:
            methods.create_scheduled_threat(
                pause=MessageSettings.SELF_DESTRUCT_TIMEOUT,
                action=methods.delete_chat_message,
                args=(current_message,)
            )
    except (ApiException, InvalidConditionError):
        methods.delete_chat_message(message)


@bot.message_handler(commands=['me'])
@methods.rude_qa_only
@methods.supergroup_only
def me_handler(message: Message):
    try:
        query = methods.prepare_query(message.text)

        if query:
            bot.send_message(message.chat.id, '*{}* _{}_'.format(message.from_user.first_name, query),
                             parse_mode=TelegramParseMode.MARKDOWN)
        methods.delete_chat_message(message)
    except (ApiException, IndexError):
        bot.send_message(
            message.chat.id, 'Братиш, наебнулось. Посмотри логи.')


@bot.message_handler(func=lambda m: m.text and m.text[:4].rstrip() in [
    ChatCommand.RO,
    ChatCommand.TO,
])
@methods.rude_qa_only
@methods.supergroup_only
def restrict_handler(message: Message):
    try:
        if message.forward_from:
            raise InvalidConditionError()
        if not methods.is_admin(message.from_user):
            raise UnauthorizedCommandError(message=message, service=methods, bot=bot, logger=logger)

        command = message.text[:3]
        task_list = {
            f'{ChatCommand.RO}': methods.set_read_only,
            f'{ChatCommand.TO}': methods.set_text_only,
        }

        try:
            target_message = message.reply_to_message
        except AttributeError:
            raise InvalidConditionError()
        if methods.is_admin(target_message.from_user):
            logger.warning(f'@{message.from_user.username} trying to restrict another admin. Abort.')
            raise InvalidConditionError()

        try:
            query = methods.prepare_query(message.text)
            restrict_duration = methods.get_duration(text=query, duration_class=RestrictDuration())
        except ParseBanDurationError:
            raise InvalidCommandError

        target_user = target_message.from_user
        try:
            logger.info(f'Try to restrict @{target_user.username} with {command} for {query}.')
            try:
                restrict_task = task_list.get(command)
                restriction_text = restrict_task(
                    user=target_user,
                    message=message,
                    duration=restrict_duration
                )
            except (KeyError, TypeError):
                raise InvalidCommandError()

            bot.send_message(
                chat_id=message.chat.id,
                text=f'*{restriction_text}*',
                reply_to_message_id=message.message_id,
                parse_mode=TelegramParseMode.MARKDOWN,
            )
        except ApiException:
            logger.error(f'Can not restrict chat member {target_user}')

    except InvalidCommandError:
        logger.warning(f'Can not execute command \'{message.text}\' from @{message.from_user.username}')
        methods.delete_chat_message(message)
    except InvalidConditionError:
        pass


@bot.message_handler(func=lambda m: m.text and m.text.strip() == ChatCommand.RW)
@methods.rude_qa_only
@methods.supergroup_only
def permit_handler(message: Message):
    try:
        if message.forward_from:
            raise InvalidConditionError()
        if not methods.is_admin(message.from_user):
            raise UnauthorizedCommandError(message=message, service=methods, bot=bot, logger=logger)

        try:
            target_message = message.reply_to_message
        except AttributeError:
            raise InvalidCommandError()

        target_user = target_message.from_user

        try:
            chat_member = bot.get_chat_member(message.chat.id, target_user.id)
            if chat_member.status != TelegramMemberStatus.RESTRICTED:
                raise InvalidConditionError()

            logger.info(f'Try to permit @{target_user.username}.')
            permission_text = methods.set_read_write(user=target_user, message=message)

            bot.send_message(
                chat_id=message.chat.id,
                text=f'*{permission_text}*',
                reply_to_message_id=message.message_id,
                parse_mode=TelegramParseMode.MARKDOWN,
            )
        except ApiException:
            logger.error(f'Can not permit chat member {target_user}')

    except InvalidCommandError:
        logger.warning(f'Can not execute command \'{message.text}\' from @{message.from_user.username}')
        methods.delete_chat_message(message)
    except InvalidConditionError:
        pass


@bot.message_handler(func=lambda m: m.text and m.text[:5].rstrip() == ChatCommand.BAN)
@methods.rude_qa_only
@methods.supergroup_only
def ban_handler(message: Message):
    try:
        if message.forward_from:
            raise InvalidConditionError()
        if not methods.is_admin(message.from_user):
            raise UnauthorizedCommandError(message=message, service=methods, bot=bot, logger=logger)

        try:
            target_message = message.reply_to_message
            if methods.is_admin(target_message.from_user):
                logger.warning(f'@{message.from_user.username} trying to ban another admin. Abort.')
                raise InvalidCommandError()
        except AttributeError:
            raise InvalidConditionError()

        try:
            query = methods.prepare_query(message.text)
            ban_duration = methods.get_duration(text=query, duration_class=BanDuration())
        except ParseBanDurationError:
            raise InvalidCommandError

        target_user = target_message.from_user
        try:
            logger.info(f'Try to ban @{target_user.username} for {query}.')
            ban_text = methods.ban_kick(
                user=target_user,
                message=message,
                duration=ban_duration
            )
            bot.send_message(
                chat_id=message.chat.id,
                text=f'*{ban_text}*',
                reply_to_message_id=message.message_id,
                parse_mode=TelegramParseMode.MARKDOWN,
            )
        except ApiException:
            logger.error(f'Can not kick chat member @{target_user.username}')

    except InvalidCommandError:
        logger.warning(f'Can not execute command \'{message.text}\' from @{message.from_user.username}')
        methods.delete_chat_message(message)
    except InvalidConditionError:
        pass


@bot.message_handler(content_types=['new_chat_members'])
@methods.rude_qa_only
def greeting_handler(message: Message):
    for new_user in message.new_chat_members:
        logger.info(f'New member joined the group: {new_user}')
        question = QuestionProvider.get_question()

        try:
            newbie_storage.add(user=new_user, timeout=message.date + question.timeout, question=question)
        except UserAlreadyInStorageError:
            return methods.timeout_kick(newbie_storage.get(new_user))

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
            methods.create_scheduled_threat(question.timeout, methods.timeout_kick, (newbie_storage.get(new_user),))
        except (UserStorageUpdateError, UserNotFoundInStorageError):
            methods.delete_chat_message(greeting_message)


@bot.message_handler(func=lambda m: m.text and m.text == ChatCommand.PASS)
@methods.rude_qa_only
@methods.supergroup_only
def pass_handler(message: Message):
    try:
        if message.forward_from:
            raise InvalidConditionError()
        if not methods.is_admin(message.from_user):
            raise UnauthorizedCommandError(message=message, service=methods, bot=bot, logger=logger)
        try:
            target_message = message.reply_to_message
        except AttributeError:
            raise InvalidConditionError()
        if target_message is None:
            raise InvalidConditionError()
        newbie_list = newbie_storage.get_user_list()
        if not newbie_list:
            raise InvalidConditionError()

        for newbie in newbie_storage:
            if newbie.greeting.message_id == target_message.message_id:
                methods.delete_chat_message(message)
                methods.delete_chat_message(newbie.greeting)
                bot.restrict_chat_member(
                    chat_id=target_message.chat.id,
                    user_id=newbie.user.id,
                    can_send_messages=True,
                )
                newbie_storage.remove(newbie.user)
                return
        raise InvalidConditionError()

    except ApiException:
        logger.error(f'Can not pass message')
    except InvalidConditionError:
        pass


@bot.callback_query_handler(func=lambda call: True)
def greeting_callback(call: CallbackQuery):
    try:
        if not call.message:
            raise InvalidConditionError()
        if call.from_user.id not in newbie_storage.get_user_list():
            raise InvalidConditionError()

        newbie = newbie_storage.get(call.from_user)
        greeting_message = newbie.greeting
        if call.message.message_id != greeting_message.message_id:
            raise InvalidConditionError()

        methods.remove_inline_keyboard(call.message)
        try:
            reply = newbie.question.reply[call.data]
        except (KeyError, TypeError):
            reply = '*{first_name} ответил "{call_data}".*'
        bot.send_message(
            chat_id=call.message.chat.id,
            text=reply.format(first_name=call.from_user.first_name, call_data=call.data),
            reply_to_message_id=call.message.message_id,
            parse_mode=TelegramParseMode.MARKDOWN,
        )

        newbie_storage.remove(newbie.user)
        try:
            bot.restrict_chat_member(
                chat_id=call.message.chat.id,
                user_id=call.from_user.id,
                can_send_messages=True,
            )
        except ApiException:
            logger.error(f'Can not disable restriction for chat member @{call.from_user.username}')
    except InvalidConditionError:
        pass


if __name__ == '__main__':
    bot.polling()
