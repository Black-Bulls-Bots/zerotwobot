import requests
from zerotwobot import application
from zerotwobot.modules.disable import DisableAbleCommandHandler
from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import ContextTypes


async def ud(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.effective_message
    text = message.text[len("/ud ") :]
    results = requests.get(
        f"https://api.urbandictionary.com/v0/define?term={text}",
    ).json()
    try:
        reply_text = f'*{text}*\n\n{results["list"][0]["definition"]}\n\n_{results["list"][0]["example"]}_'
    except:
        reply_text = "No results found."
    await message.reply_text(reply_text, parse_mode=ParseMode.MARKDOWN)


UD_HANDLER = DisableAbleCommandHandler(["ud"], ud, block=False)

application.add_handler(UD_HANDLER)

__command_list__ = ["ud"]
__handlers__ = [UD_HANDLER]
