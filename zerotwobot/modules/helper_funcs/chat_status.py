from time import perf_counter
from functools import wraps
from cachetools import TTLCache
from threading import RLock
from zerotwobot import (
    DEL_CMDS,
    DEV_USERS,
    DRAGONS,
    SUPPORT_CHAT,
    DEMONS,
    TIGERS,
    WOLVES,
    application,
)

from telegram import (
    Chat, 
    ChatMember, 
    Update,
    ChatMemberAdministrator
)

from telegram.ext import ContextTypes
from telegram.constants import ParseMode, ChatMemberStatus

# stores admemes in memory for 10 min.
ADMIN_CACHE = TTLCache(maxsize=512, ttl=60 * 10, timer=perf_counter)
THREAD_LOCK = RLock()


def is_whitelist_plus(chat: Chat, user_id: int, member: ChatMember = None) -> bool:
    return any(user_id in user for user in [WOLVES, TIGERS, DEMONS, DRAGONS, DEV_USERS])


def is_support_plus(chat: Chat, user_id: int, member: ChatMember = None) -> bool:
    return user_id in DEMONS or user_id in DRAGONS or user_id in DEV_USERS


def is_sudo_plus(chat: Chat, user_id: int, member: ChatMember = None) -> bool:
    return user_id in DRAGONS or user_id in DEV_USERS


async def is_user_admin(chat: Chat, user_id: int, member: ChatMember = None) -> bool:
    if (
        chat.type == "private"
        or user_id in DRAGONS
        or user_id in DEV_USERS
        or user_id in [777000, 1087968824]
    ):  # Count telegram and Group Anonymous as admin
        return True
    if not member:
        with THREAD_LOCK:
            # try to fetch from cache first.
            try:
                return user_id in ADMIN_CACHE[chat.id]
            except KeyError:
                # keyerror happend means cache is deleted,
                # so query bot api again and return user status
                # while saving it in cache for future usage...
                chat_admins = await application.bot.getChatAdministrators(chat.id)
                admin_list = [x.user.id for x in chat_admins]
                ADMIN_CACHE[chat.id] = admin_list

                return user_id in admin_list
    else:
        return member.status in (ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER)


async def is_bot_admin(chat: Chat, bot_id: int, bot_member: ChatMember = None) -> bool:
    if chat.type == "private":
        return True

    if not bot_member:
        bot_member = await chat.get_member(bot_id)

    return bot_member.status in (ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER)

async def can_delete(chat: Chat, bot_id: int) -> bool:
    chat_member = await chat.get_member(bot_id)
    if isinstance(chat_member, ChatMemberAdministrator):
        return chat_member.can_delete_messages


async def is_user_ban_protected(chat: Chat, user_id: int, member: ChatMember = None) -> bool:
    if (
        chat.type == "private"
        or user_id in DRAGONS
        or user_id in DEV_USERS
        or user_id in WOLVES
        or user_id in TIGERS
        or user_id in [777000, 1087968824]
    ):  # Count telegram and Group Anonymous as admin
        return True

    if not member:
        member = await chat.get_member(user_id)

    return member.status in (ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER)

async def is_user_in_chat(chat: Chat, user_id: int) -> bool:
    member = await chat.get_member(user_id)
    return member.status in (ChatMemberStatus.LEFT, ChatMemberStatus.RESTRICTED)


def dev_plus(func):
    @wraps(func)
    async def is_dev_plus_func(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
        bot = context.bot
        user = update.effective_user

        if user.id in DEV_USERS:
            return await func(update, context, *args, **kwargs)
        elif not user:
            pass
        elif DEL_CMDS and " " not in update.effective_message.text:
            try:
                await update.effective_message.delete()
            except:
                pass
        else:
            await update.effective_message.reply_text(
                "This is a developer restricted command."
                " You do not have permissions to run this.",
            )

    return is_dev_plus_func


def sudo_plus(func):
    @wraps(func)
    async def is_sudo_plus_func(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
        bot = context.bot
        user = update.effective_user
        chat = update.effective_chat

        if user and is_sudo_plus(chat, user.id):
            return await func(update, context, *args, **kwargs)
        elif not user:
            pass
        elif DEL_CMDS and " " not in update.effective_message.text:
            try:
                await update.effective_message.delete()
            except:
                pass
        else:
            await update.effective_message.reply_text(
                "Who the hell are you to say me what to do?",
            )

    return is_sudo_plus_func


def support_plus(func):
    @wraps(func)
    async def is_support_plus_func(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
        bot = context.bot
        user = update.effective_user
        chat = update.effective_chat

        if user and is_support_plus(chat, user.id):
            return await func(update, context, *args, **kwargs)
        elif DEL_CMDS and " " not in update.effective_message.text:
            try:
                await update.effective_message.delete()
            except:
                pass

    return is_support_plus_func


def whitelist_plus(func):
    @wraps(func)
    async def is_whitelist_plus_func(
        update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs,
    ):
        bot = context.bot
        user = update.effective_user
        chat = update.effective_chat

        if user and is_whitelist_plus(chat, user.id):
            return await func(update, context, *args, **kwargs)
        else:
            await update.effective_message.reply_text(
                f"You don't have access to use this.\nVisit @{SUPPORT_CHAT}",
            )

    return is_whitelist_plus_func


def user_admin(func):
    @wraps(func)
    async def is_admin(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
        bot = context.bot
        user = update.effective_user
        chat = update.effective_chat

        if user and await is_user_admin(chat, user.id):
            return await func(update, context, *args, **kwargs)
        elif not user:
            pass
        elif DEL_CMDS and " " not in update.effective_message.text:
            try:
                await update.effective_message.delete()
            except:
                pass
        else:
            await update.effective_message.reply_text(
                "Who the hell are you to say me what to do?",
            )

    return is_admin


def user_admin_no_reply(func):
    @wraps(func)
    async def is_not_admin_no_reply(
        update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs,
    ):
        bot = context.bot
        user = update.effective_user
        chat = update.effective_chat

        if user and await is_user_admin(chat, user.id):
            return await func(update, context, *args, **kwargs)
        elif not user:
            pass
        elif DEL_CMDS and " " not in update.effective_message.text:
            try:
                await update.effective_message.delete()
            except:
                pass

    return is_not_admin_no_reply


def user_not_admin(func):
    @wraps(func)
    async def is_not_admin(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
        bot = context.bot
        user = update.effective_user
        chat = update.effective_chat

        if user and not await is_user_admin(chat, user.id):
            return await func(update, context, *args, **kwargs)
        elif not user:
            pass

    return is_not_admin


def bot_admin(func):
    @wraps(func)
    async def is_admin(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
        bot = context.bot
        chat = update.effective_chat
        update_chat_title = chat.title
        message_chat_title = update.effective_message.chat.title

        if update_chat_title == message_chat_title:
            not_admin = "I'm not admin!"
        else:
            not_admin = f"I'm not admin in <b>{update_chat_title}</b>!"

        if await is_bot_admin(chat, bot.id):
            return await func(update, context, *args, **kwargs)
        else:
            await update.effective_message.reply_text(not_admin, parse_mode=ParseMode.HTML)

    return is_admin


def bot_can_delete(func):
    @wraps(func)
    async def delete_rights(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
        bot = context.bot
        chat = update.effective_chat
        update_chat_title = chat.title
        message_chat_title = update.effective_message.chat.title

        if update_chat_title == message_chat_title:
            cant_delete = "I can't delete messages here!\nMake sure I'm admin and can delete other user's messages."
        else:
            cant_delete = f"I can't delete messages in <b>{update_chat_title}</b>!\nMake sure I'm admin and can delete other user's messages there."

        if await can_delete(chat, bot.id):
            return await func(update, context, *args, **kwargs)
        else:
            await update.effective_message.reply_text(cant_delete, parse_mode=ParseMode.HTML)

    return delete_rights


def can_pin(func):
    @wraps(func)
    async def pin_rights(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
        bot = context.bot
        chat = update.effective_chat
        update_chat_title = chat.title
        message_chat_title = update.effective_message.chat.title

        if update_chat_title == message_chat_title:
            cant_pin = (
                "I can't pin messages here!\nMake sure I'm admin and can pin messages."
            )
        else:
            cant_pin = f"I can't pin messages in <b>{update_chat_title}</b>!\nMake sure I'm admin and can pin messages there."
        
        bot_member = await chat.get_member(bot.id)

        if isinstance(bot_member, ChatMemberAdministrator):
            if bot_member.can_pin_messages:
                return await func(update, context, *args, **kwargs)
            else:
                await update.effective_message.reply_text(cant_pin, parse_mode=ParseMode.HTML)

    return pin_rights


def can_promote(func):
    @wraps(func)
    async def promote_rights(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
        bot = context.bot
        chat = update.effective_chat
        update_chat_title = chat.title
        message_chat_title = update.effective_message.chat.title

        if update_chat_title == message_chat_title:
            cant_promote = "I can't promote/demote people here!\nMake sure I'm admin and can appoint new admins."
        else:
            cant_promote = (
                f"I can't promote/demote people in <b>{update_chat_title}</b>!\n"
                f"Make sure I'm admin there and can appoint new admins."
            )
        bot_member = await chat.get_member(bot.id)

        if isinstance(bot_member, ChatMemberAdministrator):
            if bot_member.can_promote_members:
                return await func(update, context, *args, **kwargs)
            else:
                await update.effective_message.reply_text(cant_promote, parse_mode=ParseMode.HTML)

    return promote_rights


def can_restrict(func):
    @wraps(func)
    async def restrict_rights(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
        bot = context.bot
        chat = update.effective_chat
        update_chat_title = chat.title
        message_chat_title = update.effective_message.chat.title

        if update_chat_title == message_chat_title:
            cant_restrict = "I can't restrict people here!\nMake sure I'm admin and can restrict users."
        else:
            cant_restrict = f"I can't restrict people in <b>{update_chat_title}</b>!\nMake sure I'm admin there and can restrict users."
        
        bot_member = await chat.get_member(bot.id)

        if isinstance(bot_member, ChatMemberAdministrator):
            if bot_member.can_restrict_members:
                return await func(update, context, *args, **kwargs)
            else:
                await update.effective_message.reply_text(
                    cant_restrict, parse_mode=ParseMode.HTML,
                )

    return restrict_rights

def connection_status(func):
    @wraps(func)
    async def connected_status(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
        conn = await connected(
            context.bot,
            update,
            update.effective_chat,
            update.message.from_user.id,
            need_admin=False,
        )

        if conn:
            chat = await application.bot.getChat(conn)
            update.__setattr__("_effective_chat", chat)
            return await func(update, context, *args, **kwargs)
        else:
            if update.effective_message.chat.type == "private":
                await update.effective_message.reply_text(
                    "Send /connect in a group that you and I have in common first.",
                )
                return connected_status

            return await func(update, context, *args, **kwargs)

    return connected_status


# Workaround for circular import with connection.py
from zerotwobot.modules import connection

connected = connection.connected
