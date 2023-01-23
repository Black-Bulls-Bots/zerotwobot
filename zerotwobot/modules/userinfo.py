from datetime import datetime
import html
from html import escape
import os
import re

import humanize
from telegram import ChatMemberAdministrator, Update
from telegram.constants import ChatID, ParseMode, ChatType
from telegram.error import BadRequest
from telegram.ext import CommandHandler, ContextTypes
from telegram.helpers import mention_html
from telethon import events
from telethon.tl.functions.channels import GetFullChannelRequest
from telethon.tl.types import ChannelParticipantsAdmins
from zerotwobot import (DEV_USERS, DRAGONS, INFOPIC, LOGGER, OWNER_ID,
                        application)
from zerotwobot import telethn as ZerotwoTelethonClient
from zerotwobot.__main__ import STATS, TOKEN, USER_INFO
from zerotwobot.modules.disable import DisableAbleCommandHandler
from zerotwobot.modules.helper_funcs.chat_status import check_admin
from zerotwobot.modules.helper_funcs.extraction import extract_user
from zerotwobot.modules.sql.afk_sql import check_afk_status, is_afk
from zerotwobot.modules.sql.approve_sql import is_approved
from zerotwobot.modules.users import get_user_id


async def get_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    bot, args = context.bot, context.args
    chat = update.effective_chat
    message = update.effective_message
    user_id = await extract_user(message, context, args)

    if message.reply_to_message:
        if chat.is_forum and message.reply_to_message.forum_topic_created:
            await message.reply_text(
                f"This group's id is <code>:{chat.id}</code> \nThis topic's id is <code>{message.message_thread_id}</code>",
                parse_mode=ParseMode.HTML,
            )
            return
    else:
        pass
            
    if message.reply_to_message and message.reply_to_message.forward_from:

        user1 = message.reply_to_message.from_user
        user2 = message.reply_to_message.forward_from

        await message.reply_text(
            f"<b>Telegram ID:</b>,\n"
            f"• {html.escape(user2.first_name)} - <code>{user2.id}</code>.\n"
            f"• {html.escape(user1.first_name)} - <code>{user1.id}</code>.",
            parse_mode=ParseMode.HTML,
        )
    elif len(args) >= 1 or message.reply_to_message:
        user = await bot.get_chat(user_id)
        await message.reply_text(
            f"{html.escape(user.first_name)}'s id is <code>{user.id}</code>.",
            parse_mode=ParseMode.HTML,
        )
    elif chat.type == "private":
        await message.reply_text(
            f"Your id is <code>{chat.id}</code>.", parse_mode=ParseMode.HTML,
        )
    else:
        await message.reply_text(
        f"This group's id is <code>{chat.id}</code>.", parse_mode=ParseMode.HTML,
        )
    return

@ZerotwoTelethonClient.on(
    events.NewMessage(
        pattern="/ginfo ", from_users=(DRAGONS or []),
    ),
)
async def group_info(event) -> None:
    chat = event.text.split(" ", 1)[1]
    try:
        entity = await event.client.get_entity(chat)
        totallist = await event.client.get_participants(
            entity, filter=ChannelParticipantsAdmins,
        )
        ch_full = await event.client(GetFullChannelRequest(channel=entity))
    except:
        await event.reply(
            "Can't for some reason, maybe it is a private one or that I am banned there.",
        )
        return
    msg = f"**ID**: `{entity.id}`"
    msg += f"\n**Title**: `{entity.title}`"
    try:
        msg += f"\n**Datacenter**: `{entity.photo.dc_id}`"
        msg += f"\n**Video PFP**: `{entity.photo.has_video}`"
    except:
        pass
    msg += f"\n**Supergroup**: `{entity.megagroup}`"
    msg += f"\n**Restricted**: `{entity.restricted}`"
    msg += f"\n**Scam**: `{entity.scam}`"
    msg += f"\n**Slowmode**: `{entity.slowmode_enabled}`"
    if entity.username:
        msg += f"\n**Username**: {entity.username}"
    msg += "\n\n**Member Stats:**"
    msg += f"\n`Admins:` `{len(totallist)}`"
    msg += f"\n`Users`: `{totallist.total}`"
    msg += "\n\n**Admins List:**"
    for x in totallist:
        msg += f"\n• [{x.id}](tg://user?id={x.id})"
    msg += f"\n\n**Description**:\n`{ch_full.full_chat.about}`"
    await event.reply(msg)



async def gifid(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.effective_message
    if msg.reply_to_message and msg.reply_to_message.animation and not msg.reply_to_message.forum_topic_created:
        await update.effective_message.reply_text(
            f"Gif ID:\n<code>{msg.reply_to_message.animation.file_id}</code>",
            parse_mode=ParseMode.HTML,
        )
    else:
        await update.effective_message.reply_text("Please reply to a gif to get its ID.")

async def info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    message = update.effective_message
    args = context.args
    bot = context.bot

    head = ""
    premium = False

    reply = await message.reply_text("<code>Getting Information...</code>", parse_mode=ParseMode.HTML)

    if len(args) >= 1 and args[0][0] == "@":
        user_name = args[0]
        user_id = await get_user_id(user_name)

        if not user_id:
            try:
                chat_obj = await bot.get_chat(user_name)
            except BadRequest:
                await reply.edit_text("I can't get information about this user/channel/group.")
                return
            userid = chat_obj.id
        else:
            userid = user_id
    elif len(args) >= 1 and args[0].lstrip("-").isdigit():
        userid = int(args[0])
    elif message.reply_to_message and not message.reply_to_message.forum_topic_created:
        if message.reply_to_message.sender_chat:
            userid = message.reply_to_message.sender_chat.id
        elif message.reply_to_message.from_user:
            if message.reply_to_message.from_user.id == ChatID.FAKE_CHANNEL:
                userid = message.reply_to_message.chat.id
            else:
                userid = message.reply_to_message.from_user.id
                premium = message.reply_to_message.from_user.is_premium
    elif not message.reply_to_message and not args:
        if message.from_user.id == ChatID.FAKE_CHANNEL:
            userid = message.sender_chat.id
        else:
            userid = message.from_user.id
            premium = message.from_user.is_premium

    try:
        chat_obj = await bot.get_chat(userid)
    except (BadRequest, UnboundLocalError):
        await reply.edit_text("I can't get information about this user/channel/group.")
        return
    
    if chat_obj.type == ChatType.PRIVATE:
        if not chat_obj.username:
            head = f"╒═══「<b> User Information:</b> 」\n"
            await reply.edit_text("Found User, getting information...")
        elif chat_obj.username and chat_obj.username.endswith("bot"):
            head = f"╒═══「<b> Bot Information:</b> 」\n"
            await reply.edit_text("Found Bot, getting information...")
        else:
            head = f"╒═══「<b> User Information:</b> 」\n"
            await reply.edit_text("Found User, getting information...")
        head += f"<b>\nID:</b> <code>{chat_obj.id}</code>"
        head += f"<b>\nFirst Name:</b> {chat_obj.first_name}"
        if chat_obj.last_name:
            head += f"<b>\nLast Name:</b> {chat_obj.last_name}"
        if chat_obj.username:
            head += f"<b>\nUsername:</b> @{chat_obj.username}"
        head += f"\nPermalink: {mention_html(chat_obj.id, 'link')}"
        if chat_obj.username and not chat_obj.username.endswith("bot"):
            head += f"<b>\nPremium User:</b> {premium}"
        if chat_obj.bio:
            head += f"<b>\n\nBio:</b> {chat_obj.bio}"
        
        if chat.type != ChatType.PRIVATE:
            if chat_obj.id != bot.id:
                if is_afk(chat_obj.id):
                    afk_st = check_afk_status(chat_obj.id)
                    time = humanize.naturaldate(datetime.now() - afk_st.time)

                    if not afk_st.reason:
                        head += f"<b>\n\nAFK:</b> This user is away from keyboard since {time}"
                    else:
                        head += f"<b>\n\nAFK:</b> This user is away from keyboard since {time}, \nReason: {afk_st.reason}"
            
            chat_member = await chat.get_member(chat_obj.id)
            if isinstance(chat_member, ChatMemberAdministrator):
                head += f"<b>\nPresence:</b> {chat_member.status}"
                if chat_member.custom_title:
                    head += f"<b>\nAdmin Title:</b> {chat_member.custom_title}"
            else:
                head += f"<b>\nPresence:</b> {chat_member.status}"

            if is_approved(chat.id, chat_obj.id):
                head += f"<b>\nApproved:</b> This user is approved in this chat."
        
        disaster_level_present = False

        if chat_obj.id == OWNER_ID:
            head += "\n\nThe Disaster level of this person is 'God'."
            disaster_level_present = True
        elif chat_obj.id in DEV_USERS:
            head += "\n\nThis user is member of 'Black Bulls'."
            disaster_level_present = True
        elif chat_obj.id in DRAGONS:
            head += "\n\nThe Disaster level of this person is 'Dragon'."
            disaster_level_present = True
        if disaster_level_present:
            head += ' [<a href="https://t.me/blackbull_bots/49">?</a>]'.format(
                bot.username,
            )

        for mod in USER_INFO:
            try:
                mod_info = mod.__user_info__(chat_obj.id).strip()
            except TypeError:
                mod_info = mod.__user_info__(chat_obj.id, chat.id).strip()

            head += "\n\n" + mod_info if mod_info else ""
            
    if chat_obj.type == ChatType.SENDER:
        head = f"╒═══「<b>Sender Chat Information:</b> 」\n"
        await reply.edit_text("Found Sender Chat, getting information...")
        head += f"<b>\nID:</b> <code>{chat_obj.id}</code>"
        if chat_obj.title:
            head += f"<b>\nTitle:</b> {chat_obj.title}"
        if chat_obj.username:
            head += f"<b>\nUsername:</b> @{chat_obj.username}"
        head += f"\nPermalink: {mention_html(chat_obj.id, 'link')}"
        if chat_obj.description:
            head += f"<b>\n\nDescription:</b> {chat_obj.description}"

    elif chat_obj.type == ChatType.CHANNEL:
        head = f"╒═══「<b> Channel Information:</b> 」\n"
        await reply.edit_text("Found Channel, getting information...")
        head += f"<b>\nID:</b> <code>{chat_obj.id}</code>"
        if chat_obj.title:
            head += f"<b>\nTitle:</b> {chat_obj.title}"
        if chat_obj.username:
            head += f"<b>\nUsername:</b> @{chat_obj.username}"
        head += f"\nPermalink: {mention_html(chat_obj.id, 'link')}"
        if chat_obj.description:
            head += f"<b>\n\nDescription:</b> {chat_obj.description}"
        if chat_obj.linked_chat_id:
            head += f"<b>\nLinked Chat ID:</b> <code>{chat_obj.linked_chat_id}</code>"

    elif chat_obj.type in [ChatType.GROUP, ChatType.SUPERGROUP]:
        head = f"╒═══「<b> Group Information:</b> 」\n"
        await reply.edit_text("Found Group, getting information...")
        head += f"<b>\nID:</b> <code>{chat_obj.id}</code>"
        if chat_obj.title:
            head += f"<b>\nTitle:</b> {chat_obj.title}"
        if chat_obj.username:
            head += f"<b>\nUsername:</b> @{chat_obj.username}"
        head += f"\nPermalink: {mention_html(chat_obj.id, 'link')}"
        if chat_obj.description:
            head += f"<b>\n\nDescription:</b> {chat_obj.description}"
    
    if INFOPIC:
        try:
            if chat_obj.photo:
                _file = await chat_obj.photo.get_big_file()
                # _file = await bot.get_file(file_id)
                await _file.download_to_drive(f"{chat_obj.id}.png")

                await message.reply_photo(
                    photo=open(f"{chat_obj.id}.png", "rb"),
                    caption=(head),
                    parse_mode=ParseMode.HTML,
                )
                await reply.delete()
                os.remove(f"{chat_obj.id}.png")
            else:
                await reply.edit_text(
                escape(head), parse_mode=ParseMode.HTML, disable_web_page_preview=True,
            )

            
        except:
            await reply.edit_text(
                escape(head), parse_mode=ParseMode.HTML, disable_web_page_preview=True,
            )
    




@check_admin(only_sudo=True)
async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    stats = "<b>📊 Current stats:</b>\n" + "\n".join([mod.__stats__() for mod in STATS])
    result = re.sub(r"(\d+)", r"<code>\1</code>", stats)
    await update.effective_message.reply_text(result, parse_mode=ParseMode.HTML)


__help__ = """
*ID:*
 • `/id`*:* get the current group id. If used by replying to a message, gets that user's id.
 • `/gifid`*:* reply to a gif to me to tell you its file ID.

*Overall Information about you:*
 • `/info`*:* get information about a user.
"""


STATS_HANDLER = CommandHandler("stats", stats, block=False)
ID_HANDLER = DisableAbleCommandHandler("id", get_id, block=False)
GIFID_HANDLER = DisableAbleCommandHandler("gifid", gifid, block=False)
INFO_HANDLER = DisableAbleCommandHandler(("info", "book"), info, block=False)


application.add_handler(STATS_HANDLER)
application.add_handler(ID_HANDLER)
application.add_handler(GIFID_HANDLER)
application.add_handler(INFO_HANDLER)


__mod_name__ = "Info"
__command_list__ = ["info"]
__handlers__ = [
    ID_HANDLER,
    GIFID_HANDLER,
    INFO_HANDLER,
    STATS_HANDLER,
]
