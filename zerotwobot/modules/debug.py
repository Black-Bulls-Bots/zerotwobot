import os
import datetime

from telethon import events
from telegram import Update
from telegram.ext import ContextTypes, CommandHandler

from zerotwobot import LOGGER, telethn, application
from zerotwobot.modules.helper_funcs.chat_status import check_admin

DEBUG_MODE = False


@check_admin(only_dev=True)
async def debug(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global DEBUG_MODE
    args = update.effective_message.text.split(None, 1)
    message = update.effective_message
    if len(args) > 1:
        if args[1] in ("yes", "on"):
            DEBUG_MODE = True
            await message.reply_text("Debug mode is now on.")
        elif args[1] in ("no", "off"):
            DEBUG_MODE = False
            await message.reply_text("Debug mode is now off.")
    else:
        if DEBUG_MODE:
            await message.reply_text("Debug mode is currently on.")
        else:
            await message.reply_text("Debug mode is currently off.")


@telethn.on(events.NewMessage(pattern="[/!].*"))
async def i_do_nothing_yes(event):
    global DEBUG_MODE
    if DEBUG_MODE:
        if os.path.exists("updates.txt"):
            with open("updates.txt", "r") as f:
                text = f.read()
            with open("updates.txt", "w+") as f:
                f.write(text + f"\n-{event.from_id} ({event.chat_id}) : {event.text}")
        else:
            with open("updates.txt", "w+") as f:
                f.write(
                    f"- {event.from_id} ({event.chat_id}) : {event.text} | {datetime.datetime.now()}",
                )


support_chat = os.getenv("SUPPORT_CHAT")


@check_admin(only_dev=True)
async def logs(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    with open("log.txt", "rb") as f:
        await context.bot.send_document(document=f, filename=f.name, chat_id=user.id)


@check_admin(only_dev=True)
async def debug_log(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    message = update.effective_message
    try:
        with open("updates.txt", "rb") as f:
            await context.bot.send_document(
                document=f, filename=f.name, chat_id=user.id
            )
    except FileNotFoundError:
        LOGGER.warning(
            "updates.txt not found, means you have deleted or turned on debug mode yet"
        )
        await message.reply_text("Sorry sir, but 404")


LOG_HANDLER = CommandHandler("logs", logs, block=False)
SEND_DEBUG_HANDLER = CommandHandler("debuglog", debug_log, block=False)
DEBUG_HANDLER = CommandHandler("debug", debug, block=False)

application.add_handler(DEBUG_HANDLER)
application.add_handler(LOG_HANDLER)
application.add_handler(SEND_DEBUG_HANDLER)

__mod_name__ = "Debug"
__command_list__ = ["debug"]
__handlers__ = [DEBUG_HANDLER]
