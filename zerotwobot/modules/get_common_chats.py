import os
from time import sleep

from zerotwobot import OWNER_ID, application
from zerotwobot.modules.helper_funcs.extraction import extract_user
from zerotwobot.modules.sql.users_sql import get_user_com_chats
from telegram import Update
from telegram.error import BadRequest, RetryAfter, Forbidden
from telegram.ext import CallbackContext, CommandHandler, filters

async def get_user_common_chats(update: Update, context: CallbackContext):
    bot, args = context.bot, context.args
    msg = update.effective_message
    user = extract_user(msg, args)
    if not user:
        msg.reply_text("I share no common chats with the void.")
        return
    common_list = get_user_com_chats(user)
    if not common_list:
        msg.reply_text("No common chats with this user!")
        return
    name = await bot.get_chat(user).first_name
    text = f"<b>Common chats with {name}</b>\n"
    for chat in common_list:
        try:
            chat_name = await bot.get_chat(chat).title
            sleep(0.3)
            text += f"• <code>{chat_name}</code>\n"
        except BadRequest:
            pass
        except Forbidden:
            pass
        except RetryAfter as e:
            sleep(e.retry_after)

    if len(text) < 4096:
        msg.reply_text(text, parse_mode="HTML")
    else:
        with open("common_chats.txt", "w") as f:
            f.write(text)
        with open("common_chats.txt", "rb") as f:
            msg.reply_document(f)
        os.remove("common_chats.txt")


COMMON_CHATS_HANDLER = CommandHandler(
    "getchats", get_user_common_chats, filters=filters.User(OWNER_ID), block=False
)

application.add_handler(COMMON_CHATS_HANDLER)
