import time
from telethon import events
from telethon.errors.rpcerrorlist import MessageDeleteForbiddenError

from zerotwobot import LOGGER, telethn
from zerotwobot.modules.helper_funcs.telethn.chatstatus import (
    can_delete_messages,
    user_is_admin,
    user_can_purge,
)


async def purge_messages(event):
    start = time.perf_counter()
    if event.from_id is None:
        return

    if not await user_is_admin(
        user_id=event.sender_id, message=event
    ) and event.from_id not in [1087968824]:
        await event.reply("Only Admins are allowed to use this command")
        return

    if not await user_can_purge(user_id=event.sender_id, message=event):
        await event.reply("You don't have the permission to delete messages")
        return

    if not can_delete_messages(message=event):
        await event.reply("Can't seem to purge the message")
        return

    reply_msg = await event.get_reply_message()
    if not reply_msg:
        await event.reply("Reply to a message to select where to start purging from.")
        return
    messages = []
    message_id = reply_msg.id
    delete_to = event.message.id

    messages.append(event.reply_to_msg_id)
    for msg_id in range(message_id, delete_to + 1):
        messages.append(msg_id)
        if len(messages) == 100:
            await event.client.delete_messages(event.chat_id, messages)
            messages = []

    try:
        await event.client.delete_messages(event.chat_id, messages)
    except:
        raise
    time_ = time.perf_counter() - start
    text = f"Purged Successfully in {time_:0.2f} Second(s)"
    await event.respond(text, parse_mode="markdown")


async def delete_messages(event):
    if event.from_id is None:
        return

    if not await user_is_admin(
        user_id=event.sender_id, message=event
    ) and event.from_id not in [1087968824]:
        await event.reply("Only Admins are allowed to use this command")
        return

    if not await user_can_purge(user_id=event.sender_id, message=event):
        await event.reply("You don't have the permission to delete messages")
        return

    message = await event.get_reply_message()
    me = await telethn.get_me()
    BOT_ID = me.id

    if (
        not can_delete_messages(message=event)
        and message
        and not int(message.sender.id) == int(BOT_ID)
    ):
        if event.chat.admin_rights is None:
            return await event.reply(
                "I'm not an admin, do you mind promoting me first?"
            )
        elif not event.chat.admin_rights.delete_messages:
            return await event.reply("I don't have the permission to delete messages!")

    if not message:
        await event.reply("Whadya want to delete?")
        return
    chat = await event.get_input_chat()
    # del_message = [message, event.message]
    # Separated to make it possible for the bot to delete its own messages even if its not an admin
    await event.client.delete_messages(chat, message)
    try:
        await event.client.delete_messages(chat, event.message)
    except MessageDeleteForbiddenError:
        LOGGER.error(
            "error in deleting message {} in {}".format(event.message.id, event.chat.id)
        )
        pass


__help__ = """
*Admin only:*
 - /del: deletes the message you replied to
 - /purge: deletes all messages between this and the replied to message.
 - /purge <integer X>: deletes the replied message, and X messages following it if replied to a message.
"""

PURGE_HANDLER = purge_messages, events.NewMessage(pattern="^[!/]purge$")
DEL_HANDLER = delete_messages, events.NewMessage(pattern="^[!/]del$")

telethn.add_event_handler(*PURGE_HANDLER)
telethn.add_event_handler(*DEL_HANDLER)

__mod_name__ = "Purges"
__command_list__ = ["del", "purge"]
__handlers__ = [PURGE_HANDLER, DEL_HANDLER]
