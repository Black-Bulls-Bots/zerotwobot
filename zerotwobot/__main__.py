import importlib
import time
import re
import asyncio
from sys import argv
from typing import Optional

from zerotwobot import (
    ALLOW_EXCL,
    CERT_PATH,
    DONATION_LINK,
    LOGGER,
    OWNER_ID,
    PORT,
    TOKEN,
    URL,
    WEBHOOK,
    SUPPORT_CHAT,
    PYTHON_VERSION,
    BOT_VERSION,
    PTB_VERSION,
    BOT_API_VERSION,
    application,
    StartTime,
    telethn)

# needed to dynamically load modules
# NOTE: Module order is not guaranteed, specify that in the config file!
from zerotwobot.modules import ALL_MODULES
from zerotwobot.modules.helper_funcs.chat_status import is_user_admin
from zerotwobot.modules.helper_funcs.misc import paginate_modules
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.error import (
    BadRequest,
    ChatMigrated,
    NetworkError,
    TelegramError,
    TimedOut,
    Forbidden,
)
from telegram.ext import (
    ContextTypes,
    CallbackQueryHandler,
    CommandHandler,
    filters,
    MessageHandler,
)
from telegram.constants import ParseMode
from telegram.ext import ApplicationHandlerStop
from telegram.helpers import escape_markdown

def get_readable_time(seconds: int) -> str:
    count = 0
    ping_time = ""
    time_list = []
    time_suffix_list = ["s", "m", "h", "days"]

    while count < 4:
        count += 1
        remainder, result = divmod(seconds, 60) if count < 3 else divmod(seconds, 24)
        if seconds == 0 and remainder == 0:
            break
        time_list.append(int(result))
        seconds = int(remainder)

    for x in range(len(time_list)):
        time_list[x] = str(time_list[x]) + time_suffix_list[x]
    if len(time_list) == 4:
        ping_time += time_list.pop() + ", "

    time_list.reverse()
    ping_time += ":".join(time_list)

    return ping_time

ZEROTWO_IMG = "https://telegra.ph/file/5b9bc54b0ae753bb1ec18.jpg"

DONATE_STRING = """Heya, glad to hear you want to donate!
 You can support the project by contacting @kishoreee \
 Supporting isn't always financial! \
 Those who cannot provide monetary support are welcome to help us develop the bot at @blackbulls_support."""

IMPORTED = {}
MIGRATEABLE = []
HELPABLE = {}
STATS = []
USER_INFO = []
DATA_IMPORT = []
DATA_EXPORT = []
CHAT_SETTINGS = {}
USER_SETTINGS = {}

for module_name in ALL_MODULES:
    imported_module = importlib.import_module("zerotwobot.modules." + module_name)
    if not hasattr(imported_module, "__mod_name__"):
        imported_module.__mod_name__ = imported_module.__name__

    if imported_module.__mod_name__.lower() not in IMPORTED:
        IMPORTED[imported_module.__mod_name__.lower()] = imported_module
    else:
        raise Exception("Can't have two modules with the same name! Please change one")

    if hasattr(imported_module, "__help__") and imported_module.__help__:
        HELPABLE[imported_module.__mod_name__.lower()] = imported_module

    # Chats to migrate on chat_migrated events
    if hasattr(imported_module, "__migrate__"):
        MIGRATEABLE.append(imported_module)

    if hasattr(imported_module, "__stats__"):
        STATS.append(imported_module)

    if hasattr(imported_module, "__user_info__"):
        USER_INFO.append(imported_module)

    if hasattr(imported_module, "__import_data__"):
        DATA_IMPORT.append(imported_module)

    if hasattr(imported_module, "__export_data__"):
        DATA_EXPORT.append(imported_module)

    if hasattr(imported_module, "__chat_settings__"):
        CHAT_SETTINGS[imported_module.__mod_name__.lower()] = imported_module

    if hasattr(imported_module, "__user_settings__"):
        USER_SETTINGS[imported_module.__mod_name__.lower()] = imported_module


# do not async
async def send_help(chat_id, text, keyboard=None):
    if not keyboard:
        keyboard = InlineKeyboardMarkup(paginate_modules(0, HELPABLE, "help"))
    await application.bot.send_message(
        chat_id=chat_id,
        text=text,
        parse_mode=ParseMode.MARKDOWN,
        disable_web_page_preview=True,
        reply_markup=keyboard,
    )





async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    
    HELP_STRINGS = """
    Hey there!.
    My Name is {}, from Darling in The FranXX. Take me as your group's darling to have fun with me. \
    I can help you with the following commands.

    *Main* commands available:
    • /help: PM's you this message.
    • /help <module name>: PM's you info about that module.
    • /settings:
    • in PM: will send you your settings for all supported modules.
    • in a group: will redirect you to pm, with all that chat's settings.


    {}
    And the following:
    """.format(
        context.bot.first_name,
        "" if not ALLOW_EXCL else "\nAll commands can either be used with / or !.\n",
    )

    buttons = [
        [
            InlineKeyboardButton(
                text="Add to Group",
                url=f"https://t.me/{context.bot.username}?startgroup=True",
            ),
        ],
        [
            InlineKeyboardButton(
                "Support Group",
                "https://t.me/blackbulls_support",
            ),
            InlineKeyboardButton(
                "Announcements",
                "https://t.me/blackbull_bots"
            ),
        ],
        [
            InlineKeyboardButton(
                text="Source Code",
                url="https://github.com/Black-Bulls-Bots/zerotwobot"
            )
        ]
    ]

    args = context.args
    uptime = get_readable_time((time.time() - StartTime))
    if update.effective_chat.type == "private":
        if len(args) >= 1:
            if args[0].lower() == "help":
                await send_help(update.effective_chat.id, HELP_STRINGS)
            elif args[0].lower().startswith("ghelp_"):
                mod = args[0].lower().split("_", 1)[1]
                if not HELPABLE.get(mod, False):
                    return
                await send_help(
                    update.effective_chat.id,
                    HELPABLE[mod].__help__,
                    InlineKeyboardMarkup(
                        [[InlineKeyboardButton(text="Back", callback_data="help_back")]],
                    ),
                )
            elif args[0].lower() == "markdownhelp":
                await IMPORTED["extras"].markdown_help_sender(update)
            elif args[0].lower().startswith("stngs_"):
                match = re.match("stngs_(.*)", args[0].lower())
                chat = await application.bot.getChat(match.group(1))

                if await is_user_admin(chat, update.effective_user.id):
                    await send_settings(match.group(1), update.effective_user.id, False)
                else:
                    await send_settings(match.group(1), update.effective_user.id, True)

            elif args[0][1:].isdigit() and "rules" in IMPORTED:
                await IMPORTED["rules"].send_rules(update, args[0], from_pm=True)

        else:
            first_name = update.effective_user.first_name
            await update.effective_message.reply_photo(
                ZEROTWO_IMG,
                caption=escape_markdown(f"""                
                Hey There {first_name}. \
                \nI'm {context.bot.first_name}, made specifically to manage your group and have more fun than ever. \
                \nType /help to get available commands. \

                \nVersion info: \
                \nI'm running on v{BOT_VERSION} \
                \nPython: {PYTHON_VERSION} \
                \nPTB: {PTB_VERSION} \
                \nBOT_API: {BOT_API_VERSION}"""),
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=InlineKeyboardMarkup(buttons)
            )
    else:
        await update.effective_message.reply_text(
            "I'm running successfully on v{}\n<b>Haven't slept since:</b> <code>{}</code>".format(
                BOT_VERSION,uptime,
            ),
            parse_mode=ParseMode.HTML,
            reply_markup=InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton(
                            text="Support",
                            url="https://t.me/blackbulls_support",
                        ),
                        InlineKeyboardButton(
                            text=str("Announcement's"),
                            url="https://t.me/blackbull_bots",
                        ),
                    ],
                ],
            ),
        )


# for test purposes
async def error_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    error = context.error
    try:
        raise error
    except Forbidden:
        LOGGER.error("\nForbidden Erro\n")
        LOGGER.error(error)
        raise error
        # remove update.message.chat_id from conversation list
    except BadRequest:
        LOGGER.error("\nBadRequest Error\n")
        LOGGER.error("BadRequest caught")
        LOGGER.error(error)
        raise error

        # handle malformed requests - read more below!
    except TimedOut:
        LOGGER.error("\nTimedOut Error\n")
        raise error
        # handle slow connection problems
    except NetworkError:
        LOGGER.error("\n NetWork Error\n")
        raise error
        # handle other connection problems
    except ChatMigrated as err:
        LOGGER.error("\n ChatMigrated error\n")
        raise error
        LOGGER.error(err)
        # the chat_id of a group has changed, use e.new_chat_id instead
    except TelegramError:
        LOGGER.error(error)
        # handle all other telegram related errors



async def help_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    HELP_STRINGS = """
    Hey there!.
    My Name is {}, from Darling in The FranXX. Take me as your group's darling to have fun with me. \
    I can help you with the following commands.

    *Main* commands available:
    • /help: PM's you this message.
    • /help <module name>: PM's you info about that module.
    • /settings:
    • in PM: will send you your settings for all supported modules.
    • in a group: will redirect you to pm, with all that chat's settings.


    {}
    And the following:
    """.format(
        context.bot.first_name,
        "" if not ALLOW_EXCL else "\nAll commands can either be used with / or !.\n",
    )

    query = update.callback_query
    mod_match = re.match(r"help_module\((.+?)\)", query.data)
    prev_match = re.match(r"help_prev\((.+?)\)", query.data)
    next_match = re.match(r"help_next\((.+?)\)", query.data)
    back_match = re.match(r"help_back", query.data)

    try:
        if mod_match:
            module = mod_match.group(1)
            text = (
                "Here is the help for the *{}* module:\n".format(
                    HELPABLE[module].__mod_name__,
                )
                + HELPABLE[module].__help__
            )
            await query.message.edit_text(
                text=text,
                parse_mode=ParseMode.MARKDOWN,
                disable_web_page_preview=True,
                reply_markup=InlineKeyboardMarkup(
                    [[InlineKeyboardButton(text="Back", callback_data="help_back")]],
                ),
            )

        elif prev_match:
            curr_page = int(prev_match.group(1))
            await query.message.edit_text(
                text=HELP_STRINGS,
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=InlineKeyboardMarkup(
                    paginate_modules(curr_page - 1, HELPABLE, "help"),
                ),
            )

        elif next_match:
            next_page = int(next_match.group(1))
            await query.message.edit_text(
                text=HELP_STRINGS,
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=InlineKeyboardMarkup(
                    paginate_modules(next_page + 1, HELPABLE, "help"),
                ),
            )

        elif back_match:
            await query.message.edit_text(
                text=HELP_STRINGS,
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=InlineKeyboardMarkup(
                    paginate_modules(0, HELPABLE, "help"),
                ),
            )

        # ensure no spinny white circle
        await context.bot.answer_callback_query(query.id)
        # await query.message.delete()

    except BadRequest:
        pass



async def get_help(update: Update, context: ContextTypes.DEFAULT_TYPE):

    HELP_STRINGS = """
    Hey there!.
    My Name is {}, from Darling in The FranXX. Take me as your group's darling to have fun with me. \
    I can help you with the following commands.

    *Main* commands available:
    • /help: PM's you this message.
    • /help <module name>: PM's you info about that module.
    • /settings:
    • in PM: will send you your settings for all supported modules.
    • in a group: will redirect you to pm, with all that chat's settings.


    {}
    And the following:
    """.format(
        context.bot.first_name,
        "" if not ALLOW_EXCL else "\nAll commands can either be used with / or !.\n",
    )

    chat = update.effective_chat  # type: Optional[Chat]
    args = update.effective_message.text.split(None, 1)  # type: ignore

    # ONLY send help in PM
    if chat.type != chat.PRIVATE:   # type: ignore
        if len(args) >= 2 and any(args[1].lower() == x for x in HELPABLE):
            module = args[1].lower()
            await update.effective_message.reply_text(
                f"Contact me in PM to get help of {module.capitalize()}",
                reply_markup=InlineKeyboardMarkup(
                    [
                        [
                            InlineKeyboardButton(
                                text="Help",
                                url="t.me/{}?start=ghelp_{}".format(
                                    context.bot.username, module,
                                ),
                            ),
                        ],
                    ],
                ),
            )
            return
        await update.effective_message.reply_text(                                      # type: ignore
            "Contact me in PM to get the list of possible commands.",
            reply_markup=InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton(
                            text="Help",
                            url="t.me/{}?start=help".format(context.bot.username),
                        ),
                    ],
                ],
            ),
        )
        return

    elif len(args) >= 2 and any(args[1].lower() == x for x in HELPABLE):
        module = args[1].lower()
        text = (
            "Here is the available help for the *{}* module:\n".format(
                HELPABLE[module].__mod_name__,
            )
            + HELPABLE[module].__help__
        )
        await send_help(
            chat.id,
            text,
            InlineKeyboardMarkup(
                [[InlineKeyboardButton(text="Back", callback_data="help_back")]],
            ),
        )

    else:
        await send_help(chat.id, HELP_STRINGS)


async def send_settings(chat_id, user_id, user=False):
    if user:
        if USER_SETTINGS:
            settings = "\n\n".join(
                "*{}*:\n{}".format(mod.__mod_name__, mod.__user_settings__(user_id))
                for mod in USER_SETTINGS.values()
            )
            await application.bot.send_message(
                user_id,
                "These are your current settings:" + "\n\n" + settings,
                parse_mode=ParseMode.MARKDOWN,
            )

        else:
            await application.bot.send_message(
                user_id,
                "Seems like there aren't any user specific settings available :'(",
                parse_mode=ParseMode.MARKDOWN,
            )

    else:
        if CHAT_SETTINGS:
            chat_obj = await application.bot.getChat(conn)
            chat_name = chat_obj.title
            await application.bot.send_message(
                user_id,
                text="Which module would you like to check {}'s settings for Darling?".format(
                    chat_name,
                ),
                reply_markup=InlineKeyboardMarkup(
                    paginate_modules(0, CHAT_SETTINGS, "stngs", chat=chat_id),
                ),
            )
        else:
            await application.bot.send_message(
                user_id,
                "Seems like there aren't any chat settings available :'(\nSend this "
                "in a group chat you're admin in to find its current settings!",
                parse_mode=ParseMode.MARKDOWN,
            )



async def settings_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user = update.effective_user
    bot = context.bot
    mod_match = re.match(r"stngs_module\((.+?),(.+?)\)", query.data)
    prev_match = re.match(r"stngs_prev\((.+?),(.+?)\)", query.data)
    next_match = re.match(r"stngs_next\((.+?),(.+?)\)", query.data)
    back_match = re.match(r"stngs_back\((.+?)\)", query.data)
    try:
        if mod_match:
            chat_id = mod_match.group(1)
            module = mod_match.group(2)
            chat = await bot.get_chat(chat_id)
            text = "*{}* has the following settings for the *{}* module:\n\n".format(
                escape_markdown(chat.title), CHAT_SETTINGS[module].__mod_name__,
            ) + CHAT_SETTINGS[module].__chat_settings__(chat_id, user.id)
            await query.message.reply_text(
                text=text,
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=InlineKeyboardMarkup(
                    [
                        [
                            InlineKeyboardButton(
                                text="Back",
                                callback_data="stngs_back({})".format(chat_id),
                            ),
                        ],
                    ],
                ),
            )

        elif prev_match:
            chat_id = prev_match.group(1)
            curr_page = int(prev_match.group(2))
            chat = await bot.get_chat(chat_id)
            await query.message.reply_text(
                "Hi there! There are quite a few settings for {} - go ahead and pick what "
                "you're interested in.".format(chat.title),
                reply_markup=InlineKeyboardMarkup(
                    paginate_modules(
                        curr_page - 1, CHAT_SETTINGS, "stngs", chat=chat_id,
                    ),
                ),
            )

        elif next_match:
            chat_id = next_match.group(1)
            next_page = int(next_match.group(2))
            chat = await bot.get_chat(chat_id)
            await query.message.reply_text(
                "Hi there! There are quite a few settings for {} - go ahead and pick what "
                "you're interested in.".format(chat.title),
                reply_markup=InlineKeyboardMarkup(
                    paginate_modules(
                        next_page + 1, CHAT_SETTINGS, "stngs", chat=chat_id,
                    ),
                ),
            )

        elif back_match:
            chat_id = back_match.group(1)
            chat = await bot.get_chat(chat_id)
            await query.message.reply_text(
                text="Hi there! There are quite a few settings for {} - go ahead and pick what "
                "you're interested in.".format(escape_markdown(chat.title)),
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=InlineKeyboardMarkup(
                    paginate_modules(0, CHAT_SETTINGS, "stngs", chat=chat_id),
                ),
            )

        # ensure no spinny white circle
        await bot.answer_callback_query(query.id)
        await query.message.delete()
    except BadRequest as excp:
        if excp.message not in [
            "Message is not modified",
            "Query_id_invalid",
            "Message can't be deleted",
        ]:
            LOGGER.exception("Exception in settings buttons. %s", str(query.data))



async def get_settings(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat  # type: Optional[Chat]
    user = update.effective_user  # type: Optional[User]
    msg = update.effective_message  # type: Optional[Message]

    # ONLY send settings in PM
    if chat.type != chat.PRIVATE:
        if await is_user_admin(chat, user.id):
            text = "Click here to get this chat's settings, as well as yours."
            await msg.reply_text(
                text,
                reply_markup=InlineKeyboardMarkup(
                    [
                        [
                            InlineKeyboardButton(
                                text="Settings",
                                url="t.me/{}?start=stngs_{}".format(
                                    context.bot.username, chat.id,
                                ),
                            ),
                        ],
                    ],
                ),
            )
        else:
            text = "Click here to check your settings."

    else:
        await send_settings(chat.id, user.id, True)



async def donate(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_message.from_user
    chat = update.effective_chat  # type: Optional[Chat]
    bot = context.bot
    if chat.type == "private":
        await update.effective_message.reply_text(
            DONATE_STRING, parse_mode=ParseMode.MARKDOWN, disable_web_page_preview=True,
        )

        if OWNER_ID != 1638803785 and DONATION_LINK:
            await update.effective_message.reply_text(
                "You can also donate to the person currently running me "
                "[here]({})".format(DONATION_LINK),
                parse_mode=ParseMode.MARKDOWN,
            )

    else:
        try:
            await bot.send_message(
                user.id,
                DONATE_STRING,
                parse_mode=ParseMode.MARKDOWN,
                disable_web_page_preview=True,
            )

            await update.effective_message.reply_text(
                "I've PM'ed you about donating to my creator!",
            )
        except Forbidden:
            await update.effective_message.reply_text(
                "Contact me in PM first to get donation information.",
            )


async def migrate_chats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.effective_message  # type: Optional[Message]
    if msg.migrate_to_chat_id:
        old_chat = update.effective_chat.id
        new_chat = msg.migrate_to_chat_id
    elif msg.migrate_from_chat_id:
        old_chat = msg.migrate_from_chat_id
        new_chat = update.effective_chat.id
    else:
        return

    LOGGER.info("Migrating from %s, to %s", str(old_chat), str(new_chat))
    for mod in MIGRATEABLE:
        mod.__migrate__(old_chat, new_chat)

    LOGGER.info("Successfully migrated!")
    raise ApplicationHandlerStop


def main():

    start_handler = CommandHandler("start", start, block=False)

    help_handler = CommandHandler("help", get_help, block=False)
    help_callback_handler = CallbackQueryHandler(help_button, pattern=r"help_.*", block=False)

    settings_handler = CommandHandler("settings", get_settings, block=False)
    settings_callback_handler = CallbackQueryHandler(settings_button, pattern=r"stngs_", block=False)

    donate_handler = CommandHandler("donate", donate, block=False)
    migrate_handler = MessageHandler(filters.StatusUpdate.MIGRATE, migrate_chats, block=False)

    application.add_handler(start_handler)
    application.add_handler(help_handler)
    application.add_handler(settings_handler)
    application.add_handler(help_callback_handler)
    application.add_handler(settings_callback_handler)
    application.add_handler(migrate_handler)
    application.add_handler(donate_handler)

    application.add_error_handler(error_callback)

    if WEBHOOK:
        LOGGER.info("Using webhooks.")
        application.run_webhook(listen="0.0.0.0", port=PORT, url_path=TOKEN)
    else:
        LOGGER.info("Using long polling.")
        application.run_polling(timeout=15, drop_pending_updates=False)   

    if len(argv) not in (1, 3, 4):
        telethn.disconnect()
    else:
        telethn.run_until_disconnected()

         
if __name__ == "__main__":
    LOGGER.info("Successfully loaded modules: " + str(ALL_MODULES))
    telethn.start(bot_token=TOKEN)
    main()