# Module to blacklist users and prevent them from using commands by @TheRealPhoenix
import html
import zerotwobot.modules.sql.blacklistusers_sql as sql
from zerotwobot import (
    DEV_USERS,
    OWNER_ID,
    DRAGONS,
    application,
)
from zerotwobot.modules.helper_funcs.chat_status import check_admin
from zerotwobot.modules.helper_funcs.extraction import (
    extract_user,
    extract_user_and_text,
)
from zerotwobot.modules.log_channel import gloggable
from telegram import Update
from telegram.constants import ParseMode
from telegram.error import BadRequest
from telegram.ext import ContextTypes, CommandHandler
from telegram.helpers import mention_html

BLACKLISTWHITELIST = [OWNER_ID] + DEV_USERS + DRAGONS
BLABLEUSERS = [OWNER_ID] + DEV_USERS


@gloggable
@check_admin(only_dev=True)
async def bl_user(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
    message = update.effective_message
    user = update.effective_user
    bot, args = context.bot, context.args
    user_id, reason = await extract_user_and_text(message, context, args)

    if not user_id:
        await message.reply_text("I doubt that's a user.")
        return ""

    if user_id == bot.id:
        await message.reply_text(
            "How am I supposed to do my work if I am ignoring myself?"
        )
        return ""

    if user_id in BLACKLISTWHITELIST:
        await message.reply_text("No!\nNoticing Disasters is my job.")
        return ""

    try:
        target_user = await bot.get_chat(user_id)
    except BadRequest as excp:
        if excp.message == "User not found":
            await message.reply_text("I can't seem to find this user.")
            return ""
        else:
            raise

    sql.blacklist_user(user_id, reason)
    await message.reply_text("I shall ignore the existence of this user!")
    log_message = (
        f"#BLACKLIST\n"
        f"<b>Admin:</b> {mention_html(user.id, html.escape(user.first_name))}\n"
        f"<b>User:</b> {mention_html(target_user.id, html.escape(target_user.first_name))}"
    )
    if reason:
        log_message += f"\n<b>Reason:</b> {reason}"

    return log_message


@check_admin(only_dev=True)
@gloggable
async def unbl_user(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
    message = update.effective_message
    user = update.effective_user
    bot, args = context.bot, context.args
    user_id = await extract_user(message, context, args)

    if not user_id:
        await message.reply_text("I doubt that's a user.")
        return ""

    if user_id == bot.id:
        await message.reply_text("I always notice myself.")
        return ""

    try:
        target_user = await bot.get_chat(user_id)
    except BadRequest as excp:
        if excp.message == "User not found":
            await message.reply_text("I can't seem to find this user.")
            return ""
        else:
            raise

    if sql.is_user_blacklisted(user_id):

        sql.unblacklist_user(user_id)
        await message.reply_text("*notices user*")
        log_message = (
            f"#UNBLACKLIST\n"
            f"<b>Admin:</b> {mention_html(user.id, html.escape(user.first_name))}\n"
            f"<b>User:</b> {mention_html(target_user.id, html.escape(target_user.first_name))}"
        )

        return log_message

    else:
        await message.reply_text("I am not ignoring them at all though!")
        return ""


@check_admin(only_dev=True)
async def bl_users(update: Update, context: ContextTypes.DEFAULT_TYPE):
    users = []
    bot = context.bot
    for each_user in sql.BLACKLIST_USERS:
        user = await bot.get_chat(each_user)
        reason = sql.get_reason(each_user)

        if reason:
            users.append(
                f"• {mention_html(user.id, html.escape(user.first_name))} :- {reason}",
            )
        else:
            users.append(f"• {mention_html(user.id, html.escape(user.first_name))}")

    message = "<b>Blacklisted Users</b>\n"
    if not users:
        message += "Noone is being ignored as of yet."
    else:
        message += "\n".join(users)

    await update.effective_message.reply_text(message, parse_mode=ParseMode.HTML)


def __user_info__(user_id):
    is_blacklisted = sql.is_user_blacklisted(user_id)

    text = "Blacklisted: <b>{}</b>"
    if user_id in [777000, 1087968824]:
        return ""
    if user_id == application.bot.id:
        return ""
    if int(user_id) in DRAGONS:
        return ""
    if is_blacklisted:
        text = text.format("Yes")
        reason = sql.get_reason(user_id)
        if reason:
            text += f"\nReason: <code>{reason}</code>"
    else:
        text = text.format("No")

    return text


BL_HANDLER = CommandHandler("ignore", bl_user, block=False)
UNBL_HANDLER = CommandHandler("notice", unbl_user, block=False)
BLUSERS_HANDLER = CommandHandler("ignoredlist", bl_users, block=False)

application.add_handler(BL_HANDLER)
application.add_handler(UNBL_HANDLER)
application.add_handler(BLUSERS_HANDLER)

__mod_name__ = "Blacklisting Users"
__handlers__ = [BL_HANDLER, UNBL_HANDLER, BLUSERS_HANDLER]
