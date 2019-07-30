import logging

from telebot import TeleBot
from telebot.apihelper import ApiException
from telebot.types import Message, CallbackQuery

from .const import TelegramChatType, EnvVar, TelegramParseMode, LoggingSettings, BanDuration
from .dto import NewbieDto
from .env_loader import EnvLoader
from .error import ParseBanDurationError, NewbieAlreadyInStorageError, NewbieStorageUpdateError
from .greeting import QuestionProvider, NewbieStorage
from .notification import Notification
from .utils import BotUtils

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


@bot.message_handler(func=lambda m: m.text == 'ping')
def ping_handler(message: Message):
    bot.send_message(message.chat.id, 'pong')


@bot.message_handler(func=lambda m: m.chat.type == TelegramChatType.SUPER_GROUP, commands=['me'])
def me_irc(message: Message):
    if message.chat.id == methods.chat_id:
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


@bot.message_handler(
    func=lambda m:
    m.content_type == 'text' and m.text[:4].rstrip() in ['!ro', '!to'] and m.chat.type == TelegramChatType.SUPER_GROUP
)
def read_only_handler(message: Message):
    if message.chat.id == methods.chat_id:
        try:
            admin_list = [x.user.id for x in bot.get_chat_administrators(message.chat.id)]

            if message.from_user.id in admin_list:
                target_message = message.reply_to_message
                if target_message.from_user.id in admin_list:
                    logger.warning('Try to restrict another admin. Abort.')
                    return
            else:
                logger.warning('Try to use restrict command from non-factor user. Reflect!')
                target_message = message

            query = methods.prepare_query(message.text)
            restrict_duration = methods.get_duration(query)

            target_user = target_message.from_user
            try:
                logger.info(f'Try to use restrict @{target_user.username} for {query}.')
                if message.text[:3] == '!ro':
                    bot.restrict_chat_member(
                        chat_id=message.chat.id,
                        user_id=target_user.id,
                        until_date=message.date + restrict_duration.seconds,
                        can_send_messages=False
                    )
                    ban_message = notification.read_only(
                        first_name=target_user.first_name,
                        duration_text=restrict_duration.text,
                    )
                if message.text[:3] == '!to':
                    bot.restrict_chat_member(
                        chat_id=message.chat.id,
                        user_id=target_user.id,
                        until_date=message.date + restrict_duration.seconds,
                        can_send_messages=True,
                        can_send_media_messages=False,
                    )
                    ban_message = notification.text_only(
                        first_name=target_user.first_name,
                        duration_text=restrict_duration.text,
                    )
                bot.send_message(message.chat.id, f'*{ban_message}*', parse_mode=TelegramParseMode.MARKDOWN)
            except ApiException:
                logger.error(f'Can not restrict chat member {target_user}')

        except ParseBanDurationError:
            try:
                bot.delete_message(message.chat.id, message.message_id)
            except ApiException:
                logger.error(f'Can not delete chat message {message}')


@bot.message_handler(content_types=['new_chat_members'])
def greeting_handler(message: Message):
    if message.chat.id == methods.chat_id:
        for new_user in message.new_chat_members:
            logger.info(f'New member joined the group: {new_user}')
            question = QuestionProvider.get_question()

            try:
                newbie_storage.add(user=new_user, timeout=message.date + question.timeout, question=question)
            except NewbieAlreadyInStorageError:
                return timeout_kick(newbie_storage.get(new_user))

            logger.info(f'Trying to temporary restrict all users content for @{new_user.username}')
            try:
                bot.restrict_chat_member(
                    chat_id=message.chat.id,
                    user_id=new_user.id,
                    until_date=message.date + question.timeout * 2,
                    can_send_messages=False
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
            except NewbieStorageUpdateError:
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


@bot.message_handler()
def timeout_handler(message: Message):
    if len(newbie_storage.get_user_list()) > 0:
        for newbie in newbie_storage.get_expired(message.date):
            timeout_kick(newbie)


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
    kick_message = bot.send_message(
        chat_id=greeting_message.chat.id,
        text=f'*{user.first_name} пиздует из чата, потому что не ответил на вопрос.*',
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


if __name__ == '__main__':
    bot.polling()
