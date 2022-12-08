from datetime import datetime
from functools import wraps

from telegram.ext import ContextTypes
from telegram.constants import ChatType
from zerotwobot.modules.helper_funcs.misc import is_module_loaded
# from zerotwobot.modules.sql.topics_sql import get_action_topic

FILENAME = __name__.rsplit(".", 1)[-1]

if is_module_loaded(FILENAME):
    from telegram import Update
    from telegram.constants import ParseMode
    from telegram.error import BadRequest, Forbidden
    from telegram.ext import CommandHandler, JobQueue
    from telegram.helpers import escape_markdown

    from zerotwobot import EVENT_LOGS, LOGGER, application
    from zerotwobot.modules.helper_funcs.chat_status import check_admin
    from zerotwobot.modules.sql import log_channel_sql as sql

    def loggable(func):
        @wraps(func)
        async def log_action(
            update: Update,
            context: ContextTypes.DEFAULT_TYPE,
            job_queue: JobQueue = None,
            *args,
            **kwargs,
        ):
            if not job_queue:
                result = await func(update, context, *args, **kwargs)
            else:
                result = await func(update, context, job_queue, *args, **kwargs)

            chat = update.effective_chat
            message = update.effective_message

            if result and isinstance(result, str):
                datetime_fmt = "%H:%M - %d-%m-%Y"
                result += f"\n<b>Event Stamp</b>: <code>{datetime.utcnow().strftime(datetime_fmt)}</code>"

                if chat.is_forum and chat.username:
                    result += f'\n<b>Link:</b> <a href="https://t.me/{chat.username}/{message.message_thread_id}/{message.message_id}">click here</a>'
            
                if message.chat.type == chat.SUPERGROUP and message.chat.username:
                    result += f'\n<b>Link:</b> <a href="https://t.me/{chat.username}/{message.message_id}">click here</a>'
                log_chat = sql.get_chat_log_channel(chat.id)
                if log_chat:
                    await send_log(context, log_chat, chat.id, result)

            return result

        return log_action

    def gloggable(func):
        @wraps(func)
        async def glog_action(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
            result = await func(update, context, *args, **kwargs)
            chat = update.effective_chat
            message = update.effective_message

            if result:
                datetime_fmt = "%H:%M - %d-%m-%Y"
                result += "\n<b>Event Stamp</b>: <code>{}</code>".format(
                    datetime.utcnow().strftime(datetime_fmt),
                )
                if chat.is_forum and chat.username:
                    result += f'\n<b>Link:</b> <a href="https://t.me/{chat.username}/{message.message_thread_id}/{message.message_id}">click here</a>'
                elif message.chat.type == chat.SUPERGROUP and message.chat.username:
                    result += f'\n<b>Link:</b> <a href="https://t.me/{chat.username}/{message.message_id}">click here</a>'
                log_chat = str(EVENT_LOGS)
                if log_chat:
                    await send_log(context, log_chat, chat.id, result)

            return result

        return glog_action

    async def send_log(
        context: ContextTypes.DEFAULT_TYPE, log_chat_id: str, orig_chat_id: str, result: str,
    ):
        bot = context.bot
        # topic_chat = get_action_topic(orig_chat_id)
        try:
            await bot.send_message(
                log_chat_id,
                result,
                parse_mode=ParseMode.HTML,
                disable_web_page_preview=True,
            )
        except BadRequest as excp:
            if excp.message == "Chat not found":
                try:
                    await bot.send_message(
                        orig_chat_id, "This log channel has been deleted - unsetting.",
                        message_thread_id= 1
                    )
                except:
                    await bot.send_message(
                    orig_chat_id, "This log channel has been deleted - unsetting.",
                )
                sql.stop_chat_logging(orig_chat_id)
            else:
                LOGGER.warning(excp.message)
                LOGGER.warning(result)
                LOGGER.exception("Could not parse")

                await bot.send_message(
                    log_chat_id,
                    result
                    + "\n\nFormatting has been disabled due to an unexpected error.",
                )

    
    @check_admin(is_user=True)
    async def logging(update: Update, context: ContextTypes.DEFAULT_TYPE):
        bot = context.bot
        message = update.effective_message
        chat = update.effective_chat

        log_channel = sql.get_chat_log_channel(chat.id)
        if log_channel:
            log_channel_info = await bot.get_chat(log_channel)
            await message.reply_text(
                f"This group has all it's logs sent to:"
                f" {escape_markdown(log_channel_info.title)} (`{log_channel}`)",
                parse_mode=ParseMode.MARKDOWN,
            )

        else:
            await message.reply_text("No log channel has been set for this group!")


    @check_admin(is_user=True)
    async def setlog(update: Update, context: ContextTypes.DEFAULT_TYPE):
        bot = context.bot
        message = update.effective_message
        chat = update.effective_chat
        if chat.type == ChatType.CHANNEL:
            await bot.send_message(
                chat.id,
                "Now, forward the /setlog to the group you want to tie this channel to!",
            )

        elif message.forward_from_chat:
            sql.set_chat_log_channel(chat.id, message.forward_from_chat.id)

            try:
                await bot.send_message(
                    message.forward_from_chat.id,
                    f"This channel has been set as the log channel for {chat.title or chat.first_name}.",
                )
            except Forbidden as excp:
                if excp.message == "Forbidden: bot is not a member of the channel chat":
                    if chat.is_forum:
                        await bot.send_message(chat.id, "Successfully set log channel!", message_thread_id=message.message_thread_id)
                    else:
                        await bot.send_message(chat.id, "Successfully set log channel!")
                else:
                    LOGGER.exception("ERROR in setting the log channel.")

            if chat.is_forum:
                await bot.send_message(chat.id, "Successfully set log channel!", message_thread_id=message.message_thread_id)
            else:
                await bot.send_message(chat.id, "Successfully set log channel!")

        else:
            await message.reply_text(
                "The steps to set a log channel are:\n"
                " - add bot to the desired channel\n"
                " - send /setlog to the channel\n"
                " - forward the /setlog to the group\n",
            )

    
    @check_admin(is_user=True)
    async def unsetlog(update: Update, context: ContextTypes.DEFAULT_TYPE):
        bot = context.bot
        message = update.effective_message
        chat = update.effective_chat

        log_channel = sql.stop_chat_logging(chat.id)
        if log_channel:
            await bot.send_message(
                log_channel, f"Channel has been unlinked from {chat.title}",
            )
            await message.reply_text("Log channel has been un-set.")

        else:
            await message.reply_text("No log channel has been set yet!")

    def __stats__():
        return f"• {sql.num_logchannels()} log channels set."

    def __migrate__(old_chat_id, new_chat_id):
        sql.migrate_chat(old_chat_id, new_chat_id)

    async def __chat_settings__(chat_id, user_id):
        log_channel = sql.get_chat_log_channel(chat_id)
        if log_channel:
            log_channel_info = await application.bot.get_chat(log_channel)
            return f"This group has all it's logs sent to: {escape_markdown(log_channel_info.title)} (`{log_channel}`)"
        return "No log channel is set for this group!"

    __help__ = """
*Admins only:*
• `/logchannel`*:* get log channel info
• `/setlog`*:* set the log channel.
• `/unsetlog`*:* unset the log channel.

Setting the log channel is done by:
• adding the bot to the desired channel (as an admin!)
• sending `/setlog` in the channel
• forwarding the `/setlog` to the group
"""

    __mod_name__ = "Log Channels"

    LOG_HANDLER = CommandHandler("logchannel", logging, block=False)
    SET_LOG_HANDLER = CommandHandler("setlog", setlog, block=False)
    UNSET_LOG_HANDLER = CommandHandler("unsetlog", unsetlog, block=False)

    application.add_handler(LOG_HANDLER)
    application.add_handler(SET_LOG_HANDLER)
    application.add_handler(UNSET_LOG_HANDLER)

else:
    # run anyway if module not loaded
    def loggable(func):
        return func

    def gloggable(func):
        return func
