import traceback

from httpx import AsyncClient
import html
import random
import sys
import pretty_errors
import io
import os
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes, CommandHandler
from zerotwobot import application, DEV_USERS, OWNER_ID

pretty_errors.mono()


class ErrorsDict(dict):
    "A custom dict to store errors and their count"

    def __init__(self, *args, **kwargs):
        self.raw = []
        super().__init__(*args, **kwargs)

    def __contains__(self, error):
        self.raw.append(error)
        error.identifier = "".join(random.choices("ABCDEFGHIJKLMNOPQRSTUVWXYZ", k=5))
        for e in self:
            if type(e) is type(error) and e.args == error.args:
                self[e] += 1
                return True
        self[error] = 0
        return False

    def __len__(self):
        return len(self.raw)


errors = ErrorsDict()


async def error_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update:
        return
    if context.error in errors:
        return
    try:
        stringio = io.StringIO()
        pretty_errors.output_stderr = stringio
        output = pretty_errors.excepthook(
            type(context.error),
            context.error,
            context.error.__traceback__,
        )
        pretty_errors.output_stderr = sys.stderr
        pretty_error = stringio.getvalue()
        stringio.close()
    except:
        pretty_error = "Failed to create pretty error."
    tb_list = traceback.format_exception(
        None,
        context.error,
        context.error.__traceback__,
    )
    tb = "".join(tb_list)
    pretty_message = (
        f"{pretty_error}\n"
        "-------------------------------------------------------------------------------\n"
        "An exception was raised while handling an update\n"
        f"User: {update.effective_user.id}\n"
        f"Chat: {update.effective_chat.title if update.effective_chat else ''} {update.effective_chat.id if update.effective_chat else ''}\n"
        f"Callback data: {update.callback_query.data if update.callback_query else None}\n"
        f"Message: {update.effective_message.text if update.effective_message else 'No message'}\n\n"
        f"Full Traceback: {tb}"
    )
    async with AsyncClient() as client:
        r = await client.post(
            "https://nekobin.com/api/documents",
            json={"content": pretty_message},
        )
    key = r.json()
    e = html.escape(f"{context.error}")
    if not key.get("result", {}).get("key"):
        with open("error.txt", "w+") as f:
            f.write(pretty_message)
        await context.bot.send_document(
            OWNER_ID,
            open("error.txt", "rb"),
            caption=f"#{context.error.identifier}\n<b>An unknown error occured:</b>\n<code>{e}</code>",
            parse_mode="html",
        )
        if os.path.isfile("error.txt"):
            os.remove("error.txt")
        return
    key = key.get("result").get("key")
    url = f"https://nekobin.com/{key}.py"
    await context.bot.send_message(
        OWNER_ID,
        text=f"#{context.error.identifier}\n<b>An unknown error occured:</b>\n<code>{e}</code>",
        reply_markup=InlineKeyboardMarkup(
            [[InlineKeyboardButton("Nekobin", url=url)]],
        ),
        parse_mode="html",
    )


async def list_errors(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in DEV_USERS:
        return
    e = {
        k: v for k, v in sorted(errors.items(), key=lambda item: item[1], reverse=True)
    }
    msg = "<b>Errors List:</b>\n"
    for x in e:
        msg += f"• <code>{x}:</code> <b>{e[x]}</b> #{x.identifier}\n"
    msg += f"{len(errors)} have occurred since startup."
    if len(msg) > 4096:
        with open("errors_msg.txt", "w+") as f:
            f.write(msg)
        await context.bot.send_document(
            update.effective_chat.id,
            open("errors_msg.txt", "rb"),
            caption=f"Too many errors have occured..",
            parse_mode="html",
            message_thread_id=update.effective_message.message_thread_id
            if update.effective_chat.is_forum
            else None,
        )
        if os.path.isfile("errors_msg.txt"):
            os.remove("errors_msg.txt")
        return
    await update.effective_message.reply_text(msg, parse_mode="html")


application.add_error_handler(error_callback)
application.add_handler(CommandHandler("errors", list_errors))
