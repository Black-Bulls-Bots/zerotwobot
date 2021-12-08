"""
Telegraph module to upload text and image/video to telegra.ph via zerotwobot
Author/Written - @kishoreee
Copy with credits else face legal problems.
"""

import os
from datetime import datetime

from PIL import Image
from telegraph import Telegraph, exceptions, upload

from zerotwobot import TEMP_DOWNLOAD_LOC, dispatcher
from telegram import Update
from telegram.ext import CallbackContext, CommandHandler

telegrph = Telegraph()

r = telegrph.create_account(short_name="telegraph")
auth_url = r["auth_url"]

def telegraph(update: Update, context: CallbackContext):
    message = update.effective_message
    chat = update.effective_chat
    user = update.effective_user
    args = context.args
    bot = context.bot


    if not args:
        message.reply_text("Sorry invalid option \n Ex: /telegraph m - for media \n /telegraph t - for text")
        return 

    msg = message.reply_text("<code>Started telegraph module...</code>", parse_mode="html")        

    if not os.path.isdir(TEMP_DOWNLOAD_LOC):
        os.mkdir(TEMP_DOWNLOAD_LOC)


    if len(args) >= 1:
        if message.reply_to_message:
            start = datetime.now()
            reply_msg = message.reply_to_message

            if args[0] == "m":
                if reply_msg.photo:
                    file = reply_msg.photo[-1].get_file()
                    file_name = "image"
                elif reply_msg.video:
                    file = reply_msg.video.get_file()
                    file_name = reply_msg.video.file_name

                downloaded_file = file.download(TEMP_DOWNLOAD_LOC + "/" + file_name)
                msg.edit_text("<code>Downloaded image/video</code>", parse_mode="html")

                try:
                    media_url = upload.upload_file(downloaded_file)
                except exceptions.TelegraphException as exc:
                    msg.edit_text(f"ERROR: {exc}")
                else:
                    msg.edit_text(
                        f"Succesfully uploaded to [telegra.ph](https://telegra.ph{media_url[0]})",
                        parse_mode="markdown",
                    )
            elif args[0] == "t":
                if user.last_name:
                    page_title = user.first_name + " " + user.last_name
                else:
                    page_title = user.first_name

                text = reply_msg.text
                text = text.replace("\n", "<br>")

                response = telegrph.create_page(
                    page_title, html_content=text
                )

                msg.edit_text(
                    f"Successfully uploaded the Text to [telegra.ph](https://telegra.ph/{response['path']})",
                    parse_mode="markdown"
                )
                

        elif not message.reply_to_message:
            msg.edit_text("Haha! I know this trick so tag any image/video/text")


TELEGRAPH_HANDLER = CommandHandler("telegraph", telegraph, run_async=True)

dispatcher.add_handler(TELEGRAPH_HANDLER)
