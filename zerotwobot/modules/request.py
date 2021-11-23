import html

from telegram import Update, ParseMode
from telegram.error import BadRequest, Unauthorized
from telegram.ext import CallbackContext, CommandHandler, MessageHandler, Filters
from telegram.utils.helpers import mention_html

from zerotwobot import LOGGER, dispatcher
from zerotwobot.modules.sql import request_sql as sql

REQUEST_GROUP = 12

def settings(update: Update, context: CallbackContext):
    message = update.effective_message
    chat = update.effective_chat
    user = update.effective_user
    args = context.args

    if chat.type == chat.PRIVATE:
        if len(args) >= 1:
            if args[0] in ['yes', 'on']:
                sql.set_user_setting(user.id, True)
                message.reply_text(
                    "Succesfully set request handling to True\n You will now receive requests from chats you are admin."
                )
            elif args[0] in ['no', 'off']:
                sql.set_user_setting(user.id, False)
                message.reply_text(
                    "Succesfully set request handling to False\n You will not receive requests from chats you are admin."
                )
        else:
            message.reply_text(f"Current request handling preference: <code>{sql.user_should_request(user.id)}</code>", parse_mode="html")

    else:
        if len(args) >= 1:
            if args[0] in ['yes', 'on']:
                sql.set_chat_setting(chat.id, True)
                message.reply_text(
                    f"Request handling has successfully turned on in {chat.title} \n Now users can request by /request command."
                )
            elif args[0] in ['no', 'off']:
                sql.set_chat_setting(chat.id, False)
                message.reply_text(
                    f"Request handling is now turned off in {chat.title}"
                )
        else:
            message.reply_text(f"Current request handling preference: <code>{sql.chat_should_request(chat.id)}</code>", parse_mode="html")

def request(update: Update, context: CallbackContext):
    message = update.effective_message
    chat = update.effective_chat
    user = update.effective_user
    args = context.args
    bot = context.bot

    if chat and sql.chat_should_request(chat.id):
        chat_name = chat.title or chat.username or chat.first_name
        admin_list = chat.get_administrators()

        if not args:
            message.reply_text("Please give something to request")
            return ""

        if chat.type == chat.SUPERGROUP:
            request = message.text
            msg = (
                f"<b>⚠️ Request: </b>{html.escape(chat.title)}\n"
                f"<b> • Request by:</b> {mention_html(user.id, user.first_name)} | <code>{user.id}</code>\n"
                f"<b> • Content:</b> <code>{request}</code>\n"
             )
            link = f'<b> • Requested message:</b> <a href="https://t.me/{chat.username}/{message.message_id}">click here</a>'
            should_forward = False
        else:
            link = ""
            should_forward = True
            msg = f'{mention_html(user.id, user.first_name)} is requesting something in "{html.escape(chat_name)}"'

        for admin in admin_list:
            if admin.user.is_bot:
                continue

            if sql.user_should_request(admin.user.id):
                try:
                    if not chat.type == chat.SUPERGROUP:
                        bot.send_message(
                            admin.user.id, msg+link, parse_mode=ParseMode.HTML, disable_web_page_preview=True
                        )

                        if should_forward:
                            message.forward(admin.user.id)

                    if not chat.username:
                        bot.send_message(
                            admin.user.id, msg+link, parse_mode=ParseMode.HTML, disable_web_page_preview=True
                        )

                        if should_forward:
                            message.forward(admin.user.id)
                    
                    if chat.username and chat.type == chat.SUPERGROUP:

                        bot.send_message(
                            admin.user.id, msg + link, parse_mode=ParseMode.HTML, disable_web_page_preview=True
                        )

                        if should_forward:
                            message.forward(admin.user.id)

                except Unauthorized:
                    pass
                except BadRequest as excp:
                    LOGGER.exception("Exception while requesting content!")
                
        message.reply_text(
            f"{mention_html(user.id, user.first_name)} I've submitted your request to the admins.",
            parse_mode=ParseMode.HTML,
        )
        return msg

    return ""




SETTINGS_HANDLER = CommandHandler("requests", settings, run_async=True)
REQUEST_HANDLER = CommandHandler("request", request, Filters.chat_type.groups , run_async=True)


dispatcher.add_handler(SETTINGS_HANDLER)
dispatcher.add_handler(REQUEST_HANDLER, REQUEST_GROUP)

__mod_name__ = "Request Handling"
__help__ = """
 • `/request <content>`*:*  request content to admins.

*Admins only:*
 • `/requests <on/off>`*:* change request setting, or view current status.
   • If done in pm, toggles your status.
   • If in group, toggles that groups's status.

code written by: @kishoreee
"""

__handlers__ = [
    (REQUEST_HANDLER, REQUEST_GROUP),
    (SETTINGS_HANDLER),
]