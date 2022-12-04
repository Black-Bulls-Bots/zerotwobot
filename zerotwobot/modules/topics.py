import html

from telegram import Update
from telegram.error import BadRequest
from telegram.ext import CommandHandler, ContextTypes, filters
from telegram.helpers import mention_html
from zerotwobot import application
from zerotwobot.modules.helper_funcs.chat_status import check_admin
from zerotwobot.modules.log_channel import loggable
from zerotwobot.modules.sql.topics_sql import (del_action_topic,
                                               get_action_topic,
                                               set_action_topic)


@loggable
@check_admin(permission="can_manage_topics", is_both=True)
async def set_topic_action(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.effective_message
    chat = update.effective_chat
    user = update.effective_user
    
    if chat.is_forum:
        topic_id = message.message_thread_id
        topic_chat = get_action_topic(chat.id)
        if topic_chat:
            await message.reply_text("Already a topic for actions enabled in this group, you can remove it and add new one.")
            return ""
        else:
            set_action_topic(chat.id, topic_id)
            await message.reply_text("I have successfully set this topic for actions.")
            log_message = (
                f"<b>{html.escape(chat.title)}:</b>\n"
                f"#ACTIONTOPIC\n"
                f"<b>Admin:</b> {mention_html(user.id, user.first_name)}\n"
                f"<b>Topic ID:</b>{message.message_thread_id}"
            )
            return log_message
    else:
        await message.reply_text("Action Topic can be only enabled in Groups with Topic support.")
        return ""

@loggable
@check_admin(permission="can_manage_topics", is_both=True)
async def del_topic_action(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.effective_message
    chat = update.effective_chat
    user = update.effective_user

    if chat.is_forum:
        topic_chat = get_action_topic(chat.id)
        if topic_chat:
            res = del_action_topic(chat.id)
            if res:
                await message.reply_text(f"Successfully removed the old topic ({topic_chat}) chat for actions, You can set new one now.")
                log_message = (
                    f"<b>{html.escape(chat.title)}:</b>\n"
                    f"#DELACTIONTOPIC\n"
                    f"<b>Admin:</b> {mention_html(user.id, user.first_name)}\n"
                    f"<b>Topic ID:</b>{topic_chat}"
                )
                return log_message
            else:
                await message.reply_text("I don't know this it didn't work, try again.")
                return ""
        else:
            await message.reply_text("It seems like you haven't set any topic for actions, you can set one by using /setactiontopic in the topic.")
            return ""
    else:
        await message.reply_text("Action Topic can be only removed in Groups with Topic support.")
        return ""

@loggable
@check_admin(permission="can_manage_topics", is_both=True)
async def create_topic(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.effective_message
    chat = update.effective_chat
    user = update.effective_user
    args = context.args
    
    if chat.is_forum:
        if len(args) < 1:
            await message.reply_text("You must give a name for the topic to create.")
        else:
            name = " ".join(args)
            print(name)
            try:
                topic = await context.bot.create_forum_topic(chat.id, name)
                await message.reply_text(f"Successfully created {topic.name}\nID: {topic.message_thread_id}" if topic else "Something happened")
                await context.bot.sendMessage(
                    chat_id=chat.id, 
                    text=f"Congratulations {topic.name} created successfully\nID: {topic.message_thread_id}",
                    message_thread_id=topic.message_thread_id
                )
                log_message = (
                    f"<b>{html.escape(chat.title)}:</b>\n"
                    f"#NEWTOPIC\n"
                    f"<b>Admin:</b> {mention_html(user.id, user.first_name)}\n"
                    f"<b>Topic Name:</b> {topic.name}\n"
                    f"<b>Topic ID:</b> {topic.message_thread_id}"
                )
                return log_message
            except BadRequest as e:
                await message.reply_text(f"Something happened.\n{e.message}")
                return ""
    else:
        await message.reply_text("Baka! You can create topics in topics enabled group only.") 
        return ""

@loggable
@check_admin(permission="can_manage_topics", is_both=True)
async def delete_topic(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.effective_message
    chat = update.effective_chat
    user = update.effective_user
    args = context.args
    if chat.is_forum:
        if len(args) > 0:
            try:
                topic_chat = await context.bot.delete_forum_topic(chat.id, args[0])
                if topic_chat:
                    await message.reply_text(f"Succesfully deleted {args[0]}")
                    log_message = (
                        f"<b>{html.escape(chat.title)}:</b>\n"
                        f"#DELTOPIC\n"
                        f"<b>Admin:</b> {mention_html(user.id, user.first_name)}\n"
                        f"<b>Topic ID:</b> {args[0]}"
                    )
                    return log_message
            except BadRequest as e:
                await message.reply_text(f"Something happened.\n{e.message}")
                raise
        else:
            await message.reply_text("You have to give topic ID to delete.")
            return ""
    else:
        await message.reply_text("You can perform this in topics enabled groups only.")
        return ""

@loggable
@check_admin(permission="can_manage_topics", is_both=True)
async def close_topic(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.effective_message
    chat = update.effective_chat
    user = update.effective_user
    args = context.args
    if chat.is_forum:
        if len(args) > 0:
            try:
                topic_chat = await context.bot.close_forum_topic(chat.id, args[0])
                if topic_chat:
                    await message.reply_text(f"Succesfully Closed {args[0]}")
                    log_message = (
                        f"<b>{html.escape(chat.title)}:</b>\n"
                        f"#CLOSETOPIC\n"
                        f"<b>Admin:</b> {mention_html(user.id, user.first_name)}\n"
                        f"<b>Topic ID:</b> {args[0]}"
                    )
                    return log_message
            except BadRequest as e:
                await message.reply_text(f"Something happened.\n{e.message}")
                raise
        else:
            await message.reply_text("You have to give topic ID to close.")
            return ""
    else:
        await message.reply_text("You can perform this in topics enabled groups only.")
        return ""

@loggable
@check_admin(permission="can_manage_topics", is_both=True)
async def open_topic(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.effective_message
    chat = update.effective_chat
    user = update.effective_user
    args = context.args
    if chat.is_forum:
        if len(args) > 0:
            try:
                topic_chat = await context.bot.reopen_forum_topic(chat.id, args[0])
                if topic_chat:
                    await message.reply_text(f"Succesfully Opened {args[0]}")
                    log_message = (
                        f"<b>{html.escape(chat.title)}:</b>\n"
                        f"#OPENTOPIC\n"
                        f"<b>Admin:</b> {mention_html(user.id, user.first_name)}\n"
                        f"<b>Topic ID:</b> {args[0]}"
                    )
                    return log_message
            except BadRequest as e:
                await message.reply_text(f"Something happened.\n{e.message}")
                raise
        else:
            await message.reply_text("You have to give topic ID to open.")
            return ""
    else:
        await message.reply_text("You can perform this in topics enabled groups only.")
        return ""

@loggable
@check_admin(permission="can_manage_topics", is_both=True)
async def unpin_topic(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.effective_message
    chat = update.effective_chat
    user = update.effective_user
    args = context.args
    if chat.is_forum:
        if len(args) > 0:
            try:
                topic_chat = await context.bot.reopen_forum_topic(chat.id, args[0])
                if topic_chat:
                    await message.reply_text(f"Succesfully Opened {args[0]}")
                    log_message = (
                        f"<b>{html.escape(chat.title)}:</b>\n"
                        f"#OPENTOPIC\n"
                        f"<b>Admin:</b> {mention_html(user.id, user.first_name)}\n"
                        f"<b>Topic ID:</b> {args[0]}"
                    )
                    return log_message
            except BadRequest as e:
                await message.reply_text(f"Something happened.\n{e.message}")
                raise
        else:
            await message.reply_text("You have to give topic ID to open.")
            return ""
    else:
        await message.reply_text("You can perform this in topics enabled groups only.")
        return ""

__mod_name__ = "Topics"

__help__ = """
Telegram introuduced new way of managing your chat called Forums(Topics)

As a group management bot I have some useful commands to help you
create, delete, close and reopen topics in your chat.

• `/setactiontopic`*:* Set issuing topic for action messages such as welcome, goodbye, warns, bans,..etc
• `/delactiontopic`*:* Delete default topic for actions messages.
• `/topicnew`*:* Create new topic, requires topic name to create.
• `/topicdel`*:* Delete an existing topic, requires topic ID to delete.  
• `/topicclose`*:* Close an existing topic, requires topic ID to close.
• `/topicopen`*:* Open an already closed topic, requires topic ID to open.  
"""

SET_TOPIC_HANDLER = CommandHandler("setactiontopic", set_topic_action, block=False)
DEL_TOPIC_HANDLER = CommandHandler("delactiontopic", del_topic_action, block=False)
CREATE_TOPIC_HANDLER = CommandHandler("topicnew", create_topic, block=False)
DELETE_TOPIC_HANDLER = CommandHandler("topicdel", delete_topic, block=False)
CLOSE_TOPIC_HANDLER = CommandHandler("topicclose", close_topic, block=False)
OPEN_TOPIC_HANDLER = CommandHandler("topicopen", open_topic, block=False)

application.add_handler(SET_TOPIC_HANDLER)
application.add_handler(DEL_TOPIC_HANDLER)
application.add_handler(CREATE_TOPIC_HANDLER)
application.add_handler(DELETE_TOPIC_HANDLER)
application.add_handler(CLOSE_TOPIC_HANDLER)
application.add_handler(OPEN_TOPIC_HANDLER)


__command_list__ = [
    "setactiontopic",
    "delactiontopic",
    "topicnew",
    "topicclose",
    "topicopen",
]

__handlers__ = [
    SET_TOPIC_HANDLER,
    DEL_TOPIC_HANDLER,
    CREATE_TOPIC_HANDLER,
    DELETE_TOPIC_HANDLER,
    CLOSE_TOPIC_HANDLER,
    OPEN_TOPIC_HANDLER,
]