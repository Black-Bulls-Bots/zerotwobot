import html
import re
import os
import requests

from telethon.tl.functions.channels import GetFullChannelRequest
from telethon.tl.types import ChannelParticipantsAdmins, updates
from telethon import events

from telegram import Update, MessageEntity
from telegram.constants import ParseMode
from telegram.ext import ContextTypes, CommandHandler
from telegram.error import BadRequest
from telegram.helpers import escape_markdown, mention_html

from zerotwobot import (
    DEV_USERS,
    OWNER_ID,
    DRAGONS,
    DEMONS,
    TIGERS,
    WOLVES,
    INFOPIC,
    application,
)
from zerotwobot.__main__ import STATS, TOKEN, USER_INFO
from zerotwobot.modules.disable import DisableAbleCommandHandler
from zerotwobot.modules.sql.global_bans_sql import is_user_gbanned
from zerotwobot.modules.sql.afk_sql import is_afk, check_afk_status
from zerotwobot.modules.sql.users_sql import get_user_num_chats
from zerotwobot.modules.helper_funcs.chat_status import sudo_plus
from zerotwobot.modules.helper_funcs.extraction import extract_user
from zerotwobot import telethn as ZerotwoTelethonClient



async def get_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    bot, args = context.bot, context.args
    message = update.effective_message
    chat = update.effective_chat
    msg = update.effective_message
    user_id = await extract_user(msg, context,  args)

    if user_id:

        if msg.reply_to_message and msg.reply_to_message.forward_from:

            user1 = message.reply_to_message.from_user
            user2 = message.reply_to_message.forward_from

            await msg.reply_text(
                f"<b>Telegram ID:</b>,"
                f"• {html.escape(user2.first_name)} - <code>{user2.id}</code>.\n"
                f"• {html.escape(user1.first_name)} - <code>{user1.id}</code>.",
                parse_mode=ParseMode.HTML,
            )

        else:

            user = await bot.get_chat(user_id)
            await msg.reply_text(
                f"{html.escape(user.first_name)}'s id is <code>{user.id}</code>.",
                parse_mode=ParseMode.HTML,
            )

    else:

        if chat.type == "private":
            await msg.reply_text(
                f"Your id is <code>{chat.id}</code>.", parse_mode=ParseMode.HTML,
            )

        else:
            await msg.reply_text(
                f"This group's id is <code>{chat.id}</code>.", parse_mode=ParseMode.HTML,
            )


@ZerotwoTelethonClient.on(
    events.NewMessage(
        pattern="/ginfo ", from_users=(TIGERS or []) + (DRAGONS or []) + (DEMONS or []),
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
    if msg.reply_to_message and msg.reply_to_message.animation:
        await update.effective_message.reply_text(
            f"Gif ID:\n<code>{msg.reply_to_message.animation.file_id}</code>",
            parse_mode=ParseMode.HTML,
        )
    else:
        await update.effective_message.reply_text("Please reply to a gif to get its ID.")



async def info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    bot, args = context.bot, context.args
    message = update.effective_message
    chat = update.effective_chat
    user_id = await extract_user(update.effective_message, args)

    if user_id:
        user = await bot.get_chat(user_id)

    elif not message.reply_to_message and not args:
        user = message.from_user

    elif not message.reply_to_message and (
        not args
        or (
            len(args) >= 1
            and not args[0].startswith("@")
            and not args[0].isdigit()
            and not message.parse_entities([MessageEntity.TEXT_MENTION])
        )
    ):
        await message.reply_text("I can't extract a user from this.")
        return

    else:
        return

    rep = await message.reply_text("<code>Appraising...</code>", parse_mode=ParseMode.HTML)

    text = (
        f"╒═══「<b> Appraisal results:</b> 」\n"
        f"ID: <code>{user.id}</code>\n"
        f"First Name: {html.escape(user.first_name)}"
    )

    if user.last_name:
        text += f"\nLast Name: {html.escape(user.last_name)}"

    if user.username:
        text += f"\nUsername: @{html.escape(user.username)}"

    text += f"\nPermalink: {mention_html(user.id, 'link')}"

    if chat.type != "private" and user_id != bot.id:
        _stext = "\nPresence: <code>{}</code>"

        afk_st = is_afk(user.id)
        if afk_st:
            text += _stext.format("AFK")
        else:
            status = status = await bot.get_chat_member(chat.id, user.id).status
            if status:
                if status in {"left", "kicked"}:
                    text += _stext.format("Not here")
                elif status == "member":
                    text += _stext.format("Detected")
                elif status == "administrator":
                    text += _stext.format("Admin")
                elif status == "creator":
                    text += _stext.format("Owner")
                elif status == "restricted":
                    text += _stext.format("Restricted")
    try:
        user_member = await chat.get_member(user.id)
        if user_member.status in {"administrator", "creator"}:
            custom_title = user_member.custom_title
            text += f"\n\nTitle:\n<b>{custom_title}</b>"
    except BadRequest:
        pass

    disaster_level_present = False

    if user.id == OWNER_ID:
        text += "\n\nThe Disaster level of this person is 'God'."
        disaster_level_present = True
    elif user.id in DEV_USERS:
        text += "\n\nThis user is member of 'Black Bulls'."
        disaster_level_present = True
    elif user.id in DRAGONS:
        text += "\n\nThe Disaster level of this person is 'Dragon'."
        disaster_level_present = True
    elif user.id in DEMONS:
        text += "\n\nThe Disaster level of this person is 'Demon'."
        disaster_level_present = True
    elif user.id in TIGERS:
        text += "\n\nThe Disaster level of this person is 'Tiger'."
        disaster_level_present = True
    elif user.id in WOLVES:
        text += "\n\nThe Disaster level of this person is 'Wolf'."
        disaster_level_present = True

    if disaster_level_present:
        text += ' [<a href="https://t.me/blackbull_bots/49">?</a>]'.format(
            bot.username,
        )


    for mod in USER_INFO:
        try:
            mod_info = mod.__user_info__(user.id).strip()
        except TypeError:
            mod_info = mod.__user_info__(user.id, chat.id).strip()
        if mod_info:
            text += "\n\n" + mod_info

    if INFOPIC:
        try:
            profile = await context.bot.get_user_profile_photos(user.id).photos[0][-1]
            _file = await bot.get_file(profile["file_id"])
            _file.download(f"{user.id}.png")

            await message.reply_photo(
                photo=open(f"{user.id}.png", "rb"),
                caption=(text),
                parse_mode=ParseMode.HTML,
            )

            os.remove(f"{user.id}.png")
        # Incase user don't have profile pic, send normal text
        except IndexError:
            await message.reply_text(
                text, parse_mode=ParseMode.HTML, disable_web_page_preview=True,
            )

    else:
        await message.reply_text(
            text, parse_mode=ParseMode.HTML, disable_web_page_preview=True,
        )

    rep.delete()





@sudo_plus
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
