from restriction import RestrictionStorage

__version__ = '1.0.8'

import logging

from telebot import TeleBot
from telebot.apihelper import ApiException
from telebot.types import Message, CallbackQuery

from const import EnvVar, TelegramParseMode, LoggingSettings, RestrictCommand, \
    MessageSettings
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
    RestrictCommand.RO,
    RestrictCommand.TO,
])
@methods.rude_qa_only
@methods.supergroup_only
def restrict_handler(message: Message):
    try:
        if message.forward_from:
            raise InvalidConditionError()

        command = message.text[:3]
        task_list = {
            f'{RestrictCommand.RO}': methods.set_read_only,
            f'{RestrictCommand.TO}': methods.set_text_only,
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
            logger.info(f'Try to restrict @{target_user.username} with {command} for {query}.')
            methods.check_current_restrictions(target_user, message, restrict_duration, command)
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


@bot.callback_query_handler(func=lambda call: True)
def greeting_callback(call: CallbackQuery):
    if call.message and call.from_user.id in newbie_storage.get_user_list():
        methods.remove_inline_keyboard(call.message)
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


if __name__ == '__main__':
    bot.polling()
