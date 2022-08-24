import os
import subprocess
import sys

from contextlib import suppress
from time import sleep

import zerotwobot

from zerotwobot import application
from zerotwobot.modules.helper_funcs.chat_status import dev_plus
from telegram import Update
from telegram.error import Forbidden, TelegramError
from telegram.ext import CallbackContext, CommandHandler


@dev_plus
async def allow_groups(update: Update, context: CallbackContext):
    args = context.args
    if not args:
        state = "Lockdown is " + "on" if not zerotwobot.ALLOW_CHATS else "off"
        await update.effective_message.reply_text(f"Current state: {state}")
        return
    if args[0].lower() in ["off", "no"]:
        zerotwobot.ALLOW_CHATS = True
    elif args[0].lower() in ["yes", "on"]:
        zerotwobot.ALLOW_CHATS = False
    else:
        await update.effective_message.reply_text("Format: /lockdown Yes/No or Off/On")
        return
    await update.effective_message.reply_text("Done! Lockdown value toggled.")


@dev_plus
async def leave(update: Update, context: CallbackContext):
    bot = context.bot
    args = context.args
    if args:
        chat_id = str(args[0])
        try:
            await bot.leave_chat(int(chat_id))
        except TelegramError:
            await update.effective_message.reply_text(
                "Beep boop, I could not leave that group(dunno why tho).",
            )
            return
        with suppress(Forbidden):
            await update.effective_message.reply_text("Beep boop, I left that soup!.")
    else:
        await update.effective_message.reply_text("Send a valid chat ID")



LEAVE_HANDLER = CommandHandler("leave", leave, block=False)

ALLOWGROUPS_HANDLER = CommandHandler("lockdown", allow_groups, block=False)

application.add_handler(ALLOWGROUPS_HANDLER)
application.add_handler(LEAVE_HANDLER)


__mod_name__ = "Dev"
__handlers__ = [LEAVE_HANDLER, ALLOWGROUPS_HANDLER]
