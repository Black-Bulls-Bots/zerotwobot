from zerotwobot import application, LOGGER
from zerotwobot.modules.helper_funcs.chat_status import (
    bot_admin,
    is_bot_admin,
    is_user_ban_protected,
    is_user_in_chat,
)
from zerotwobot.modules.helper_funcs.extraction import extract_user_and_text

from telegram import Update, ChatPermissions, ChatMemberAdministrator, ChatMemberRestricted
from telegram.error import BadRequest
from telegram.ext import filters, ContextTypes, CommandHandler

RBAN_ERRORS = {
    "User is an administrator of the chat",
    "Chat not found",
    "Not enough rights to restrict/unrestrict chat member",
    "User_not_participant",
    "Peer_id_invalid",
    "Group chat was deactivated",
    "Need to be inviter of a user to kick it from a basic group",
    "Chat_admin_required",
    "Only the creator of a basic group can kick group administrators",
    "Channel_private",
    "Not in the chat",
}

RUNBAN_ERRORS = {
    "User is an administrator of the chat",
    "Chat not found",
    "Not enough rights to restrict/unrestrict chat member",
    "User_not_participant",
    "Peer_id_invalid",
    "Group chat was deactivated",
    "Need to be inviter of a user to kick it from a basic group",
    "Chat_admin_required",
    "Only the creator of a basic group can kick group administrators",
    "Channel_private",
    "Not in the chat",
}

RKICK_ERRORS = {
    "User is an administrator of the chat",
    "Chat not found",
    "Not enough rights to restrict/unrestrict chat member",
    "User_not_participant",
    "Peer_id_invalid",
    "Group chat was deactivated",
    "Need to be inviter of a user to kick it from a basic group",
    "Chat_admin_required",
    "Only the creator of a basic group can kick group administrators",
    "Channel_private",
    "Not in the chat",
}

RMUTE_ERRORS = {
    "User is an administrator of the chat",
    "Chat not found",
    "Not enough rights to restrict/unrestrict chat member",
    "User_not_participant",
    "Peer_id_invalid",
    "Group chat was deactivated",
    "Need to be inviter of a user to kick it from a basic group",
    "Chat_admin_required",
    "Only the creator of a basic group can kick group administrators",
    "Channel_private",
    "Not in the chat",
}

RUNMUTE_ERRORS = {
    "User is an administrator of the chat",
    "Chat not found",
    "Not enough rights to restrict/unrestrict chat member",
    "User_not_participant",
    "Peer_id_invalid",
    "Group chat was deactivated",
    "Need to be inviter of a user to kick it from a basic group",
    "Chat_admin_required",
    "Only the creator of a basic group can kick group administrators",
    "Channel_private",
    "Not in the chat",
}



@bot_admin
async def rban(update: Update, context: ContextTypes.DEFAULT_TYPE):
    bot, args = context.bot, context.args
    message = update.effective_message

    if not args:
        await message.reply_text("You don't seem to be referring to a chat/user.")
        return

    user_id, chat_id = await extract_user_and_text(message, context, args)

    if not user_id:
        await message.reply_text(
            "You don't seem to be referring to a user or the ID specified is incorrect..",
        )
        return
    elif not chat_id:
        await message.reply_text("You don't seem to be referring to a chat.")
        return

    try:
        chat = await bot.get_chat(chat_id.split()[0])
    except BadRequest as excp:
        if excp.message == "Chat not found":
            await message.reply_text(
                "Chat not found! Make sure you entered a valid chat ID and I'm part of that chat.",
            )
            return
        else:
            raise

    if chat.type == "private":
        await message.reply_text("I'm sorry, but that's a private chat!")
        return

    bot_member = await chat.get_member(bot.id)

    if isinstance(bot_member, ChatMemberAdministrator):
        bot_can_restrict_members = bot_member.can_restrict_members

        if (
            not await is_bot_admin(chat, bot.id)
            or not await bot_can_restrict_members
        ):
            await message.reply_text(
                "I can't restrict people there! Make sure I'm admin and can ban users.",
            )
            return

    try:
        member = await chat.get_member(user_id)
    except BadRequest as excp:
        if excp.message == "User not found":
            await message.reply_text("I can't seem to find this user")
            return
        else:
            raise

    if await is_user_ban_protected(chat, user_id, member):
        await message.reply_text("I really wish I could ban admins...")
        return

    if user_id == bot.id:
        await message.reply_text("I'm not gonna BAN myself, are you crazy?")
        return

    try:
        await chat.ban_member(user_id)
        await message.reply_text("Banned from chat!")
    except BadRequest as excp:
        if excp.message == "Reply message not found":
            # Do not reply
            await message.reply_text("Banned!", quote=False)
        elif excp.message in RBAN_ERRORS:
            await message.reply_text(excp.message)
        else:
            LOGGER.warning(update)
            LOGGER.exception(
                "ERROR banning user %s in chat %s (%s) due to %s",
                user_id,
                chat.title,
                chat.id,
                excp.message,
            )
            await message.reply_text("Well damn, I can't ban that user.")



@bot_admin
async def runban(update: Update, context: ContextTypes.DEFAULT_TYPE):
    bot, args = context.bot, context.args
    message = update.effective_message

    if not args:
        await message.reply_text("You don't seem to be referring to a chat/user.")
        return

    user_id, chat_id = await extract_user_and_text(message, context, args)

    if not user_id:
        await message.reply_text(
            "You don't seem to be referring to a user or the ID specified is incorrect..",
        )
        return
    elif not chat_id:
        await message.reply_text("You don't seem to be referring to a chat.")
        return

    try:
        chat = await bot.get_chat(chat_id.split()[0])
    except BadRequest as excp:
        if excp.message == "Chat not found":
            await message.reply_text(
                "Chat not found! Make sure you entered a valid chat ID and I'm part of that chat.",
            )
            return
        else:
            raise

    if chat.type == "private":
        await message.reply_text("I'm sorry, but that's a private chat!")
        return
    
    bot_member = await chat.get_member(bot.id)

    if isinstance(bot_member, ChatMemberAdministrator):
        bot_can_restrict_members = bot_member.can_restrict_members

        if (
            not await is_bot_admin(chat, bot.id)
            or not await bot_can_restrict_members
        ):
            await message.reply_text(
                "I can't unrestrict people there! Make sure I'm admin and can unban users.",
            )
            return

    try:
        member = await chat.get_member(user_id)
    except BadRequest as excp:
        if excp.message == "User not found":
            await message.reply_text("I can't seem to find this user there")
            return
        else:
            raise

    if await is_user_in_chat(chat, user_id):
        await message.reply_text(
            "Why are you trying to remotely unban someone that's already in that chat?",
        )
        return

    if user_id == bot.id:
        await message.reply_text("I'm not gonna UNBAN myself, I'm an admin there!")
        return

    try:
        chat.unban_member(user_id)
        await message.reply_text("Yep, this user can join that chat!")
    except BadRequest as excp:
        if excp.message == "Reply message not found":
            # Do not reply
            await message.reply_text("Unbanned!", quote=False)
        elif excp.message in RUNBAN_ERRORS:
            await message.reply_text(excp.message)
        else:
            LOGGER.warning(update)
            LOGGER.exception(
                "ERROR unbanning user %s in chat %s (%s) due to %s",
                user_id,
                chat.title,
                chat.id,
                excp.message,
            )
            await message.reply_text("Well damn, I can't unban that user.")



@bot_admin
async def rkick(update: Update, context: ContextTypes.DEFAULT_TYPE):
    bot, args = context.bot, context.args
    message = update.effective_message

    if not args:
        await message.reply_text("You don't seem to be referring to a chat/user.")
        return

    user_id, chat_id = await extract_user_and_text(message, context, args)

    if not user_id:
        await message.reply_text(
            "You don't seem to be referring to a user or the ID specified is incorrect..",
        )
        return
    elif not chat_id:
        await message.reply_text("You don't seem to be referring to a chat.")
        return

    try:
        chat = await bot.get_chat(chat_id.split()[0])
    except BadRequest as excp:
        if excp.message == "Chat not found":
            await message.reply_text(
                "Chat not found! Make sure you entered a valid chat ID and I'm part of that chat.",
            )
            return
        else:
            raise

    if chat.type == "private":
        await message.reply_text("I'm sorry, but that's a private chat!")
        return

    bot_member = await chat.get_member(bot.id)

    if isinstance(bot_member, ChatMemberAdministrator):
        bot_can_restrict_members = bot_member.can_restrict_members

        if (
            not await is_bot_admin(chat, bot.id)
            or not await bot_can_restrict_members
        ):
            await message.reply_text(
                "I can't restrict people there! Make sure I'm admin and can kick users.",
            )
            return

    try:
        member = await chat.get_member(user_id)
    except BadRequest as excp:
        if excp.message == "User not found":
            await message.reply_text("I can't seem to find this user")
            return
        else:
            raise

    if await is_user_ban_protected(chat, user_id, member):
        await message.reply_text("I really wish I could kick admins...")
        return

    if user_id == bot.id:
        await message.reply_text("I'm not gonna kick myself, are you crazy?")
        return

    try:
        chat.unban_member(user_id)
        await message.reply_text("kicked from chat!")
    except BadRequest as excp:
        if excp.message == "Reply message not found":
            # Do not reply
            await message.reply_text("kicked!", quote=False)
        elif excp.message in RKICK_ERRORS:
            await message.reply_text(excp.message)
        else:
            LOGGER.warning(update)
            LOGGER.exception(
                "ERROR kicking user %s in chat %s (%s) due to %s",
                user_id,
                chat.title,
                chat.id,
                excp.message,
            )
            await message.reply_text("Well damn, I can't kick that user.")



@bot_admin
async def rmute(update: Update, context: ContextTypes.DEFAULT_TYPE):
    bot, args = context.bot, context.args
    message = update.effective_message

    if not args:
        await message.reply_text("You don't seem to be referring to a chat/user.")
        return

    user_id, chat_id = await extract_user_and_text(message, context, args)

    if not user_id:
        await message.reply_text(
            "You don't seem to be referring to a user or the ID specified is incorrect..",
        )
        return
    elif not chat_id:
        await message.reply_text("You don't seem to be referring to a chat.")
        return

    try:
        chat = await bot.get_chat(chat_id.split()[0])
    except BadRequest as excp:
        if excp.message == "Chat not found":
            await message.reply_text(
                "Chat not found! Make sure you entered a valid chat ID and I'm part of that chat.",
            )
            return
        else:
            raise

    if chat.type == "private":
        await message.reply_text("I'm sorry, but that's a private chat!")
        return

    bot_member = await chat.get_member(bot.id)

    if isinstance(bot_member, ChatMemberAdministrator):
        bot_can_restrict_members = bot_member.can_restrict_members

        if (
            not await is_bot_admin(chat, bot.id)
            or not await bot_can_restrict_members
        ):
            await message.reply_text(
                "I can't restrict people there! Make sure I'm admin and can mute users.",
            )
            return

    try:
        member = await chat.get_member(user_id)
    except BadRequest as excp:
        if excp.message == "User not found":
            await message.reply_text("I can't seem to find this user")
            return
        else:
            raise

    if await is_user_ban_protected(chat, user_id, member):
        await message.reply_text("I really wish I could mute admins...")
        return

    if user_id == bot.id:
        await message.reply_text("I'm not gonna MUTE myself, are you crazy?")
        return

    try:
        await bot.restrict_chat_member(
            chat.id, user_id, permissions=ChatPermissions(can_send_messages=False),
        )
        await message.reply_text("Muted from the chat!")
    except BadRequest as excp:
        if excp.message == "Reply message not found":
            # Do not reply
            await message.reply_text("Muted!", quote=False)
        elif excp.message in RMUTE_ERRORS:
            await message.reply_text(excp.message)
        else:
            LOGGER.warning(update)
            LOGGER.exception(
                "ERROR mute user %s in chat %s (%s) due to %s",
                user_id,
                chat.title,
                chat.id,
                excp.message,
            )
            await message.reply_text("Well damn, I can't mute that user.")



@bot_admin
async def runmute(update: Update, context: ContextTypes.DEFAULT_TYPE):
    bot, args = context.bot, context.args
    message = update.effective_message

    if not args:
        await message.reply_text("You don't seem to be referring to a chat/user.")
        return

    user_id, chat_id = await extract_user_and_text(message, context, args)

    if not user_id:
        await message.reply_text(
            "You don't seem to be referring to a user or the ID specified is incorrect..",
        )
        return
    elif not chat_id:
        await message.reply_text("You don't seem to be referring to a chat.")
        return

    try:
        chat = await bot.get_chat(chat_id.split()[0])
    except BadRequest as excp:
        if excp.message == "Chat not found":
            await message.reply_text(
                "Chat not found! Make sure you entered a valid chat ID and I'm part of that chat.",
            )
            return
        else:
            raise

    if chat.type == "private":
        await message.reply_text("I'm sorry, but that's a private chat!")
        return

    bot_member = await chat.get_member(bot.id)

    if isinstance(bot_member, ChatMemberAdministrator):
        bot_can_restrict_members = bot_member.can_restrict_members

        if (
            not await is_bot_admin(chat, bot.id)
            or not await bot_can_restrict_members
        ):
            await message.reply_text(
                "I can't unrestrict people there! Make sure I'm admin and can unban users.",
            )
            return

    try:
        member = await chat.get_member(user_id)
    except BadRequest as excp:
        if excp.message == "User not found":
            await message.reply_text("I can't seem to find this user there")
            return
        else:
            raise

    if await is_user_in_chat(chat, user_id):
        if ((
            member.can_send_messages
            and member.can_send_media_messages
            and member.can_send_other_messages
            and member.can_add_web_page_previews
        ) if isinstance(member, ChatMemberRestricted) else None
        ):
            await message.reply_text("This user already has the right to speak in that chat.")
            return

    if user_id == bot.id:
        await message.reply_text("I'm not gonna UNMUTE myself, I'm an admin there!")
        return

    try:
        await bot.restrict_chat_member(
            chat.id,
            int(user_id),
            permissions=ChatPermissions(
                can_send_messages=True,
                can_send_media_messages=True,
                can_send_other_messages=True,
                can_add_web_page_previews=True,
            ),
        )
        await message.reply_text("Yep, this user can talk in that chat!")
    except BadRequest as excp:
        if excp.message == "Reply message not found":
            # Do not reply
            await message.reply_text("Unmuted!", quote=False)
        elif excp.message in RUNMUTE_ERRORS:
            await message.reply_text(excp.message)
        else:
            LOGGER.warning(update)
            LOGGER.exception(
                "ERROR unmnuting user %s in chat %s (%s) due to %s",
                user_id,
                chat.title,
                chat.id,
                excp.message,
            )
            await message.reply_text("Well damn, I can't unmute that user.")


RBAN_HANDLER = CommandHandler("rban", rban, filters=filters.User(SUDO_USERS), block=False)
RUNBAN_HANDLER = CommandHandler("runban", runban, filters=filters.User(SUDO_USERS), block=False)
RKICK_HANDLER = CommandHandler("rkick", rkick, filters=filters.User(SUDO_USERS), block=False)
RMUTE_HANDLER = CommandHandler("rmute", rmute, filters=filters.User(SUDO_USERS), block=False)
RUNMUTE_HANDLER = CommandHandler("runmute", runmute, filters=filters.User(SUDO_USERS), block=False)

application.add_handler(RBAN_HANDLER)
application.add_handler(RUNBAN_HANDLER)
application.add_handler(RKICK_HANDLER)
application.add_handler(RMUTE_HANDLER)
application.add_handler(RUNMUTE_HANDLER)
