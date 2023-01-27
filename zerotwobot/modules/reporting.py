import html

from zerotwobot import LOGGER, DRAGONS, application
from zerotwobot.modules.helper_funcs.chat_status import check_admin, user_not_admin
from zerotwobot.modules.log_channel import loggable
from zerotwobot.modules.sql import reporting_sql as sql
from telegram import Chat, InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.constants import ParseMode
from telegram.error import BadRequest, Forbidden
from telegram.ext import (
    ContextTypes,
    CallbackQueryHandler,
    CommandHandler,
    filters,
    MessageHandler,
)
from telegram.helpers import mention_html

REPORT_GROUP = 12


@check_admin(is_user=True)
async def report_setting(update: Update, context: ContextTypes.DEFAULT_TYPE):
    bot, args = context.bot, context.args
    chat = update.effective_chat
    msg = update.effective_message

    if chat.type == chat.PRIVATE:
        if len(args) >= 1:
            if args[0] in ("yes", "on"):
                sql.set_user_setting(chat.id, True)
                await msg.reply_text(
                    "Turned on reporting! You'll be notified whenever anyone reports something.",
                )

            elif args[0] in ("no", "off"):
                sql.set_user_setting(chat.id, False)
                await msg.reply_text("Turned off reporting! You wont get any reports.")
        else:
            await msg.reply_text(
                f"Your current report preference is: `{sql.user_should_report(chat.id)}`",
                parse_mode=ParseMode.MARKDOWN,
            )

    else:
        if len(args) >= 1:
            if args[0] in ("yes", "on"):
                sql.set_chat_setting(chat.id, True)
                await msg.reply_text(
                    "Turned on reporting! Admins who have turned on reports will be notified when /report "
                    "or @admin is called.",
                )

            elif args[0] in ("no", "off"):
                sql.set_chat_setting(chat.id, False)
                await msg.reply_text(
                    "Turned off reporting! No admins will be notified on /report or @admin.",
                )
        else:
            await msg.reply_text(
                f"This group's current setting is: `{sql.chat_should_report(chat.id)}`",
                parse_mode=ParseMode.MARKDOWN,
            )


@user_not_admin
@loggable
async def report(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
    bot = context.bot
    args = context.args
    message = update.effective_message
    chat = update.effective_chat
    user = update.effective_user

    if (
        chat
        and message.reply_to_message
        and not message.reply_to_message.forum_topic_created
        and sql.chat_should_report(chat.id)
    ):
        reported_user = message.reply_to_message.from_user
        chat_name = chat.title or chat.first or chat.username
        admin_list = await chat.get_administrators()
        message = update.effective_message

        if not args:
            await message.reply_text("Add a reason for reporting first.")
            return ""

        if user.id == reported_user.id:
            await message.reply_text("Uh yeah, Sure sure...maso much?")
            return ""

        if user.id == bot.id:
            await message.reply_text("Nice try.")
            return ""

        if reported_user.id in DRAGONS:
            await message.reply_text("Uh? You reporting a disaster?")
            return ""

        if chat.username and chat.type == Chat.SUPERGROUP:

            reported = f"{mention_html(user.id, user.first_name)} reported {mention_html(reported_user.id, reported_user.first_name)} to the admins!"

            msg = (
                f"<b>⚠️ Report: </b>{html.escape(chat.title)}\n"
                f"<b> • Report by:</b> {mention_html(user.id, user.first_name)}(<code>{user.id}</code>)\n"
                f"<b> • Reported user:</b> {mention_html(reported_user.id, reported_user.first_name)} (<code>{reported_user.id}</code>)\n"
            )
            link = f'<b> • Reported message:</b> <a href="https://t.me/{chat.username}/{message.reply_to_message.message_id}">click here</a>'
            should_forward = False
            keyboard = [
                [
                    InlineKeyboardButton(
                        "➡ Message",
                        url=f"https://t.me/{chat.username}/{message.reply_to_message.message_id}",
                    ),
                ],
                [
                    InlineKeyboardButton(
                        "⚠ Kick",
                        callback_data=f"report_{chat.id}=kick={reported_user.id}={reported_user.first_name}",
                    ),
                    InlineKeyboardButton(
                        "⛔️ Ban",
                        callback_data=f"report_{chat.id}=banned={reported_user.id}={reported_user.first_name}",
                    ),
                ],
                [
                    InlineKeyboardButton(
                        "❎ Delete Message",
                        callback_data=f"report_{chat.id}=delete={reported_user.id}={message.reply_to_message.message_id}",
                    ),
                ],
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
        else:
            reported = (
                f"{mention_html(user.id, user.first_name)} reported "
                f"{mention_html(reported_user.id, reported_user.first_name)} to the admins!"
            )

            msg = f'{mention_html(user.id, user.first_name)} is calling for admins in "{html.escape(chat_name)}"!'
            link = ""
            should_forward = True

        for admin in admin_list:
            if admin.user.is_bot:  # can't message bots
                continue

            if sql.user_should_report(admin.user.id):
                try:
                    if not chat.type == Chat.SUPERGROUP:
                        await bot.send_message(
                            admin.user.id,
                            msg + link,
                            parse_mode=ParseMode.HTML,
                        )

                        if should_forward:
                            await message.reply_to_message.forward(admin.user.id)

                            if (
                                len(message.text.split()) > 1
                            ):  # If user is giving a reason, send his message too
                                await message.forward(admin.user.id)
                    if not chat.username:
                        await bot.send_message(
                            admin.user.id,
                            msg + link,
                            parse_mode=ParseMode.HTML,
                        )

                        if should_forward:
                            await message.reply_to_message.forward(admin.user.id)

                            if (
                                len(message.text.split()) > 1
                            ):  # If user is giving a reason, send his message too
                                await message.forward(admin.user.id)

                    if chat.username and chat.type == Chat.SUPERGROUP:
                        await bot.send_message(
                            admin.user.id,
                            msg + link,
                            parse_mode=ParseMode.HTML,
                            reply_markup=reply_markup,
                        )

                        if should_forward:
                            await message.reply_to_message.forward(admin.user.id)

                            if (
                                len(message.text.split()) > 1
                            ):  # If user is giving a reason, send his message too
                                await message.forward(admin.user.id)

                except Forbidden:
                    pass
                except BadRequest as excp:  # TODO: cleanup exceptions
                    LOGGER.exception("Exception while reporting user")

        await message.reply_to_message.reply_text(
            f"{mention_html(user.id, user.first_name)} reported the message to the admins.",
            parse_mode=ParseMode.HTML,
        )
        return msg

    return ""


def __migrate__(old_chat_id, new_chat_id):
    sql.migrate_chat(old_chat_id, new_chat_id)


def __chat_settings__(chat_id, _):
    return f"This chat is setup to send user reports to admins, via /report and @admin: `{sql.chat_should_report(chat_id)}`"


def __user_settings__(user_id):
    if sql.user_should_report(user_id) is True:
        text = "You will receive reports from chats you're admin."
    else:
        text = "You will *not* receive reports from chats you're admin."
    return text


async def buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    bot = context.bot
    query = update.callback_query
    splitter = query.data.replace("report_", "").split("=")
    if splitter[1] == "kick":
        try:
            await bot.banChatMember(splitter[0], splitter[2])
            await bot.unbanChatMember(splitter[0], splitter[2])
            await query.answer("✅ Succesfully kicked")
            return ""
        except Exception as err:
            await query.answer("🛑 Failed to kick")
            await bot.sendMessage(
                text=f"Error: {err}",
                chat_id=query.message.chat_id,
                parse_mode=ParseMode.HTML,
            )
    elif splitter[1] == "banned":
        try:
            await bot.banChatMember(splitter[0], splitter[2])
            await query.answer("✅  Succesfully Banned")
            return ""
        except Exception as err:
            await bot.sendMessage(
                text=f"Error: {err}",
                chat_id=query.message.chat_id,
                parse_mode=ParseMode.HTML,
            )
            await query.answer("🛑 Failed to Ban")
    elif splitter[1] == "delete":
        try:
            await bot.deleteMessage(splitter[0], splitter[3])
            await query.answer("✅ Message Deleted")
            return ""
        except Exception as err:
            await bot.sendMessage(
                text=f"Error: {err}",
                chat_id=query.message.chat_id,
                parse_mode=ParseMode.HTML,
            )
            await query.answer("🛑 Failed to delete message!")


__help__ = """
 • `/report <reason>`*:* reply to a message to report it to admins.
 • `@admin`*:* reply to a message to report it to admins.
*NOTE:* Neither of these will get triggered if used by admins.

*Admins only:*
 • `/reports <on/off>`*:* change report setting, or view current status.
   • If done in pm, toggles your status.
   • If in group, toggles that groups's status.
"""

SETTING_HANDLER = CommandHandler("reports", report_setting, block=False)
REPORT_HANDLER = CommandHandler(
    "report", report, filters=filters.ChatType.GROUPS, block=False
)
ADMIN_REPORT_HANDLER = MessageHandler(
    filters.Regex(r"(?i)@admin(s)?"), report, block=False
)

REPORT_BUTTON_USER_HANDLER = CallbackQueryHandler(buttons, pattern=r"report_")
application.add_handler(REPORT_BUTTON_USER_HANDLER)

application.add_handler(SETTING_HANDLER)
application.add_handler(REPORT_HANDLER, REPORT_GROUP)
application.add_handler(ADMIN_REPORT_HANDLER, REPORT_GROUP)

__mod_name__ = "Reporting"
__handlers__ = [
    (REPORT_HANDLER, REPORT_GROUP),
    (ADMIN_REPORT_HANDLER, REPORT_GROUP),
    (SETTING_HANDLER),
]
