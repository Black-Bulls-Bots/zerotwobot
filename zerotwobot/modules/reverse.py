"""Custom zerotwo module written my kishore/joker to reverse search any image by replying
to it, or url given as args."""
import os

from GoogleSearch import Search
from telegram import (InlineKeyboardButton, InlineKeyboardMarkup,
                      MessageEntity, Update)
from telegram.error import BadRequest
from telegram.ext import ContextTypes
from zerotwobot import application
from zerotwobot.modules.disable import DisableAbleCommandHandler


async def reverse(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.effective_message
    args = context.args
    
    if args:
        if len(args) <= 1:
            url = args[0]
            if url.startswith(("https://", "http://")):
                msg = await message.reply_text("Uploading url to google..")

                result = Search(url=url)
                name = result["output"]
                link = result["similar"]
                
                await msg.edit_text("Uploaded to google, fetching results...")
                await msg.edit_text(
                text=f"{name}",
                reply_markup=InlineKeyboardMarkup(
                        [
                            [
                                InlineKeyboardButton(
                                    text="Similar",
                                    url=link,
                                ),
                            ],
                        ],
                    )
                )
                return
        else:
            await message.reply_text("Command must be used with a reply to an image or should give url")
    
    elif message.reply_to_message and message.reply_to_message.photo:
        try:
            edit = await message.reply_text("Downloading Image")
        except BadRequest:
            edit = await context.bot.send_message(update.effective_chat.id, "Downloading Image")

        photo = message.reply_to_message.photo[-1]
        file = await context.bot.get_file(photo.file_id)
        await file.download("reverse.jpg")

        await edit.edit_text("Downloaded Image, uploading to google...")

        result = Search(file_path="reverse.jpg")
        await edit.edit_text("Uploaded to google, fetching results...")
        name = result["output"]
        link = result["similar"]

        await edit.edit_text(
            text=f"{name}",
            reply_markup=InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton(
                            text="Similar",
                            url=link,
                        ),
                    ],
                ],
            )
        )
        return
    else:
        await message.reply_text("Command should be used with replying to an image or url should given.")

REVERSE_HANDLER = DisableAbleCommandHandler("reverse", reverse, block=False)
application.add_handler(REVERSE_HANDLER)

__help__ = """
Reverse search any image using google image search.

Usage:
    - sending /reverse by replying to any image
    - /reverse https://sample.com/sample.jpg
"""

__mod_name__ = "Reverse"