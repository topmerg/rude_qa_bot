import time

import telebot
from telebot import TeleBot, types

from .config import TELEGRAM_TOKEN
from .utils import BotUtils

bot = TeleBot(
    token=TELEGRAM_TOKEN,
    skip_pending=True
)

methods = BotUtils()


@bot.message_handler(func=lambda m: m.chat.id == 116233702 and m.text == "ping")
def test(message):
    bot.send_message(message.chat.id, "pong")


@bot.message_handler(func=lambda m: m.chat.type == "supergroup", commands=['me'])
def me_irc(message):
    if message.chat.id == BotUtils.RUDE_QA_CHAT_ID:
        try:
            query = methods.prepare_query(message)

            if query:
                bot.send_message(message.chat.id, '*{}* _{}_'.format(message.from_user.first_name, query),
                                 parse_mode='Markdown')
                bot.delete_message(message.chat.id, message.message_id)
            else:
                bot.delete_message(message.chat.id, message.message_id)
        except (telebot.apihelper.ApiException, IndexError):
            bot.send_message(
                message.chat.id, 'Братиш, наебнулось. Посмотри логи.')


@bot.message_handler(func=lambda m: m.text == "!ro" and m.chat.type == "supergroup")
def read_only(message):
    if message.chat.id == BotUtils.RUDE_QA_CHAT_ID:
        try:
            admin_list = [
                x.user.id for x in bot.get_chat_administrators(message.chat.id)]

            if message.from_user.id in admin_list:
                user_id = message.reply_to_message.from_user.id
                bot.restrict_chat_member(
                    message.chat.id, user_id, until_date=int(
                        time.time() + 300),
                    can_send_messages=False
                )
                ban_message = f'*{message.reply_to_message.from_user.first_name} помещен в read-only на 5 минут*'
                bot.send_message(
                    message.chat.id, ban_message, parse_mode='Markdown')
            else:
                pass
        except AttributeError:
            pass


if __name__ == '__main__':
    bot.polling()
