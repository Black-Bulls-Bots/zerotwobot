import html
from typing import Optional, List
import re

from telegram import Message, Chat, Update, User, ChatPermissions

from zerotwobot import application
from zerotwobot.modules.helper_funcs.chat_status import is_user_admin, check_admin
from zerotwobot.modules.log_channel import loggable
from zerotwobot.modules.sql import antiflood_sql as sql
from telegram.error import BadRequest
from telegram.ext import (
    ContextTypes,
    CallbackQueryHandler,
    CommandHandler,
    filters,
    MessageHandler,
)
from telegram.helpers import mention_html
from zerotwobot.modules.helper_funcs.string_handling import extract_time
from zerotwobot.modules.connection import connected
from zerotwobot.modules.helper_funcs.alternate import send_message
from zerotwobot.modules.sql.approve_sql import is_approved

FLOOD_GROUP = 3


@loggable
async def check_flood(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
    user = update.effective_user  # type: Optional[User]
    chat = update.effective_chat  # type: Optional[Chat]
    msg = update.effective_message  # type: Optional[Message]
    if not user:  # ignore channels
        return ""

    # ignore admins
    if await is_user_admin(chat, user.id):
        sql.update_flood(chat.id, None)
        return ""
    # ignore approved users
    if is_approved(chat.id, user.id):
        sql.update_flood(chat.id, None)
        return
    should_ban = sql.update_flood(chat.id, user.id)
    if not should_ban:
        return ""

    try:
        getmode, getvalue = sql.get_flood_setting(chat.id)
        if getmode == 1:
            await chat.ban_member(user.id)
            execstrings = "Banned"
            tag = "BANNED"
        elif getmode == 2:
            await chat.ban_member(user.id)
            await chat.unban_member(user.id)
            execstrings = "Kicked"
            tag = "KICKED"
        elif getmode == 3:
            await context.bot.restrict_chat_member(
                chat.id,
                user.id,
                permissions=ChatPermissions(can_send_messages=False),
            )
            execstrings = "Muted"
            tag = "MUTED"
        elif getmode == 4:
            bantime = await extract_time(msg, getvalue)
            await chat.ban_member(user.id, until_date=bantime)
            execstrings = "Banned for {}".format(getvalue)
            tag = "TBAN"
        elif getmode == 5:
            mutetime = await extract_time(msg, getvalue)
            await context.bot.restrict_chat_member(
                chat.id,
                user.id,
                until_date=mutetime,
                permissions=ChatPermissions(can_send_messages=False),
            )
            execstrings = "Muted for {}".format(getvalue)
            tag = "TMUTE"
        await send_message(
            update.effective_message,
            "Beep Boop! Boop Beep!\n{}!".format(execstrings),
        )

        return (
            "<b>{}:</b>"
            "\n#{}"
            "\n<b>User:</b> {}"
            "\nFlooded the group.".format(
                tag,
                html.escape(chat.title),
                mention_html(user.id, html.escape(user.first_name)),
            )
        )

    except BadRequest:
        await msg.reply_text(
            "I can't restrict people here, give me permissions first! Until then, I'll disable anti-flood.",
        )
        sql.set_flood(chat.id, 0)
        return (
            "<b>{}:</b>"
            "\n#INFO"
            "\nDon't have enough permission to restrict users so automatically disabled anti-flood".format(
                chat.title,
            )
        )


@check_admin(permission="can_restrict_members", is_both=True, no_reply=True)
async def flood_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    bot = context.bot
    query = update.callback_query
    user = update.effective_user
    match = re.match(r"unmute_flooder\((.+?)\)", query.data)
    if match:
        user_id = match.group(1)
        chat = update.effective_chat.id
        try:
            await bot.restrict_chat_member(
                chat,
                int(user_id),
                permissions=ChatPermissions(
                    can_send_messages=True,
                    can_send_media_messages=True,
                    can_send_other_messages=True,
                    can_add_web_page_previews=True,
                ),
            )
            await update.effective_message.edit_text(
                f"Unmuted by {mention_html(user.id, html.escape(user.first_name))}.",
                parse_mode="HTML",
            )
        except:
            pass


@loggable
@check_admin(is_user=True)
async def set_flood(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
    chat = update.effective_chat  # type: Optional[Chat]
    user = update.effective_user  # type: Optional[User]
    message = update.effective_message  # type: Optional[Message]
    args = context.args

    conn = await connected(context.bot, update, chat, user.id, need_admin=True)
    if conn:
        chat_id = conn
        chat_obj = await application.bot.getChat(conn)
        chat_name = chat_obj.title
    else:
        if update.effective_message.chat.type == "private":
            await send_message(
                update.effective_message,
                "This command is meant to use in group not in PM",
            )
            return ""
        chat_id = update.effective_chat.id
        chat_name = update.effective_message.chat.title

    if len(args) >= 1:
        val = args[0].lower()
        if val in ["off", "no", "0"]:
            await sql.set_flood(chat_id, 0)
            if conn:
                text = await message.reply_text(
                    "Antiflood has been disabled in {}.".format(chat_name),
                )
            else:
                text = await message.reply_text("Antiflood has been disabled.")

        elif val.isdigit():
            amount = int(val)
            if amount <= 0:
                await sql.set_flood(chat_id, 0)
                if conn:
                    text = await message.reply_text(
                        "Antiflood has been disabled in {}.".format(chat_name),
                    )
                else:
                    text = await message.reply_text("Antiflood has been disabled.")
                return (
                    "<b>{}:</b>"
                    "\n#SETFLOOD"
                    "\n<b>Admin:</b> {}"
                    "\nDisable antiflood.".format(
                        html.escape(chat_name),
                        mention_html(user.id, html.escape(user.first_name)),
                    )
                )

            elif amount <= 3:
                await send_message(
                    update.effective_message,
                    "Antiflood must be either 0 (disabled) or number greater than 3!",
                )
                return ""

            else:
                await sql.set_flood(chat_id, amount)
                if conn:
                    text = await message.reply_text(
                        "Anti-flood has been set to {} in chat: {}".format(
                            amount,
                            chat_name,
                        ),
                    )
                else:
                    text = await message.reply_text(
                        "Successfully updated anti-flood limit to {}!".format(amount),
                    )
                return (
                    "<b>{}:</b>"
                    "\n#SETFLOOD"
                    "\n<b>Admin:</b> {}"
                    "\nSet antiflood to <code>{}</code>.".format(
                        html.escape(chat_name),
                        mention_html(user.id, html.escape(user.first_name)),
                        amount,
                    )
                )

        else:
            await message.reply_text(
                "Invalid argument please use a number, 'off' or 'no'"
            )
    else:
        await message.reply_text(
            (
                "Use `/setflood number` to enable anti-flood.\nOr use `/setflood off` to disable antiflood!."
            ),
            parse_mode="markdown",
        )
    return ""


async def flood(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat  # type: Optional[Chat]
    user = update.effective_user  # type: Optional[User]
    msg = update.effective_message

    conn = await connected(context.bot, update, chat, user.id, need_admin=False)
    if conn:
        chat_id = conn
        chat_obj = await application.bot.getChat(conn)
        chat_name = chat_obj.title
    else:
        if update.effective_message.chat.type == "private":
            await send_message(
                update.effective_message,
                "This command is meant to use in group not in PM",
            )
            return
        chat_id = update.effective_chat.id
        chat_name = update.effective_message.chat.title

    limit = sql.get_flood_limit(chat_id)
    if limit == 0:
        if conn:
            text = await msg.reply_text(
                "I'm not enforcing any flood control in {}!".format(chat_name),
            )
        else:
            text = await msg.reply_text("I'm not enforcing any flood control here!")
    else:
        if conn:
            text = await msg.reply_text(
                "I'm currently restricting members after {} consecutive messages in {}.".format(
                    limit,
                    chat_name,
                ),
            )
        else:
            text = await msg.reply_text(
                "I'm currently restricting members after {} consecutive messages.".format(
                    limit,
                ),
            )


@check_admin(is_user=True)
async def set_flood_mode(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat  # type: Optional[Chat]
    user = update.effective_user  # type: Optional[User]
    msg = update.effective_message  # type: Optional[Message]
    args = context.args

    conn = await connected(context.bot, update, chat, user.id, need_admin=True)
    if conn:
        chat = await application.bot.getChat(conn)
        chat_id = conn
        chat_obj = await application.bot.getChat(conn)
        chat_name = chat_obj.title
    else:
        if update.effective_message.chat.type == "private":
            await send_message(
                update.effective_message,
                "This command is meant to use in group not in PM",
            )
            return ""
        chat = update.effective_chat
        chat_id = update.effective_chat.id
        chat_name = update.effective_message.chat.title

    if args:
        if args[0].lower() == "ban":
            settypeflood = "ban"
            await sql.set_flood_strength(chat_id, 1, "0")
        elif args[0].lower() == "kick":
            settypeflood = "kick"
            await sql.set_flood_strength(chat_id, 2, "0")
        elif args[0].lower() == "mute":
            settypeflood = "mute"
            await sql.set_flood_strength(chat_id, 3, "0")
        elif args[0].lower() == "tban":
            if len(args) == 1:
                teks = """It looks like you tried to set time value for antiflood but you didn't specified time; Try, `/setfloodmode tban <timevalue>`.
Examples of time value: 4m = 4 minutes, 3h = 3 hours, 6d = 6 days, 5w = 5 weeks."""
                await send_message(
                    update.effective_message, teks, parse_mode="markdown"
                )
                return
            settypeflood = "tban for {}".format(args[1])
            await sql.set_flood_strength(chat_id, 4, str(args[1]))
        elif args[0].lower() == "tmute":
            if len(args) == 1:
                teks = (
                    update.effective_message,
                    """It looks like you tried to set time value for antiflood but you didn't specified time; Try, `/setfloodmode tmute <timevalue>`.
Examples of time value: 4m = 4 minutes, 3h = 3 hours, 6d = 6 days, 5w = 5 weeks.""",
                )
                await send_message(
                    update.effective_message, teks, parse_mode="markdown"
                )
                return
            settypeflood = "tmute for {}".format(args[1])
            await sql.set_flood_strength(chat_id, 5, str(args[1]))
        else:
            await send_message(
                update.effective_message,
                "I only understand ban/kick/mute/tban/tmute!",
            )
            return
        if conn:
            text = await msg.reply_text(
                "Exceeding consecutive flood limit will result in {} in {}!".format(
                    settypeflood,
                    chat_name,
                ),
            )
        else:
            text = await msg.reply_text(
                "Exceeding consecutive flood limit will result in {}!".format(
                    settypeflood,
                ),
            )
        return (
            "<b>{}:</b>\n"
            "<b>Admin:</b> {}\n"
            "Has changed antiflood mode. User will {}.".format(
                settypeflood,
                html.escape(chat.title),
                mention_html(user.id, html.escape(user.first_name)),
            )
        )
    else:
        getmode, getvalue = await sql.get_flood_setting(chat.id)
        if getmode == 1:
            settypeflood = "ban"
        elif getmode == 2:
            settypeflood = "kick"
        elif getmode == 3:
            settypeflood = "mute"
        elif getmode == 4:
            settypeflood = "tban for {}".format(getvalue)
        elif getmode == 5:
            settypeflood = "tmute for {}".format(getvalue)
        if conn:
            text = await msg.reply_text(
                "Sending more messages than flood limit will result in {} in {}.".format(
                    settypeflood,
                    chat_name,
                ),
            )
        else:
            text = await msg.reply_text(
                "Sending more message than flood limit will result in {}.".format(
                    settypeflood,
                ),
            )
    return ""


async def __migrate__(old_chat_id, new_chat_id):
    await sql.migrate_chat(old_chat_id, new_chat_id)


def __chat_settings__(chat_id, user_id):
    limit = sql.get_flood_limit(chat_id)
    if limit == 0:
        return "Not enforcing to flood control."
    else:
        return "Antiflood has been set to`{}`.".format(limit)


__help__ = """
Antiflood allows you to take action on users that send more than x messages in a row. Exceeding the set flood \
will result in restricting that user.
 This will mute users if they send more than 10 messages in a row, bots are ignored.
 • `/flood`*:* Get the current flood control setting
• *Admins only:*
 • `/setflood <int/'no'/'off'>`*:* enables or disables flood control
 *Example:* `/setflood 10`
 • `/setfloodmode <ban/kick/mute/tban/tmute> <value>`*:* Action to perform when user have exceeded flood limit. ban/kick/mute/tmute/tban
• *Note:*
 • Value must be filled for tban and tmute!!
 It can be:
 `5m` = 5 minutes
 `6h` = 6 hours
 `3d` = 3 days
 `1w` = 1 week
 """

__mod_name__ = "Anti-Flood"

FLOOD_BAN_HANDLER = MessageHandler(
    filters.ALL & ~filters.StatusUpdate.ALL & filters.ChatType.GROUPS,
    check_flood,
    block=False,
)
SET_FLOOD_HANDLER = CommandHandler(
    "setflood", set_flood, filters=filters.ChatType.GROUPS, block=False
)
SET_FLOOD_MODE_HANDLER = CommandHandler(
    "setfloodmode", set_flood_mode, block=False
)  # , filters=filters.ChatType.GROUPS)
FLOOD_QUERY_HANDLER = CallbackQueryHandler(
    flood_button, pattern=r"unmute_flooder", block=False
)
FLOOD_HANDLER = CommandHandler(
    "flood", flood, filters=filters.ChatType.GROUPS, block=False
)

application.add_handler(FLOOD_BAN_HANDLER, FLOOD_GROUP)
application.add_handler(FLOOD_QUERY_HANDLER)
application.add_handler(SET_FLOOD_HANDLER)
application.add_handler(SET_FLOOD_MODE_HANDLER)
application.add_handler(FLOOD_HANDLER)

__handlers__ = [
    (FLOOD_BAN_HANDLER, FLOOD_GROUP),
    SET_FLOOD_HANDLER,
    FLOOD_HANDLER,
    SET_FLOOD_MODE_HANDLER,
]
