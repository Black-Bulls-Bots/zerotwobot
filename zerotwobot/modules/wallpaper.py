from random import randint

from httpx import AsyncClient
from zerotwobot import SUPPORT_CHAT, WALL_API, application
from zerotwobot.modules.disable import DisableAbleCommandHandler
from telegram import Update
from telegram.ext import ContextTypes

# Wallpapers module by @TheRealPhoenix using wall.alphacoders.com

# Need to fix this module ASAP


async def wall(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    msg = update.effective_message
    args = context.args
    msg_id = update.effective_message.message_id
    bot = context.bot
    query = " ".join(args)
    if not query:
        await msg.reply_text("Please enter a query!")
        return
    else:
        caption = query
        term = query.replace(" ", "%20")
        async with AsyncClient() as client:
            r = await client.get(
                f"https://wall.alphacoders.com/api2.0/get.php?auth={WALL_API}&method=search&term={term}"
            )
        json_rep = r.json()
        if not json_rep.get("success"):
            await msg.reply_text(f"An error occurred! Report this @{SUPPORT_CHAT}")
        else:
            wallpapers = json_rep.get("wallpapers")
            if not wallpapers:
                await msg.reply_text("No results found! Refine your search.")
                return
            else:
                index = randint(0, len(wallpapers) - 1)  # Choose random index
                wallpaper = wallpapers[index]
                wallpaper = wallpaper.get("url_image")
                wallpaper = wallpaper.replace("\\", "")
                await bot.send_photo(
                    chat_id,
                    photo=wallpaper,
                    caption="Preview",
                    reply_to_message_id=msg_id,
                    timeout=60,
                )
                await bot.send_document(
                    chat_id,
                    document=wallpaper,
                    filename="wallpaper",
                    caption=caption,
                    reply_to_message_id=msg_id,
                    timeout=60,
                )


WALLPAPER_HANDLER = DisableAbleCommandHandler("wall", wall, block=False)
application.add_handler(WALLPAPER_HANDLER)
