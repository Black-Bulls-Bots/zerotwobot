import wikipedia
from zerotwobot import application
from zerotwobot.modules.disable import DisableAbleCommandHandler
from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import ContextTypes
from wikipedia.exceptions import DisambiguationError, PageError

async def wiki(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = (
        update.effective_message.reply_to_message
        if update.effective_message.reply_to_message and not update.effective_message.reply_to_message.forum_topic_created
        else update.effective_message
    )
    res = ""
    if msg == update.effective_message:
        search = msg.text.split(" ", maxsplit=1)[1]
    else:
        search = msg.text
    try:
        res = wikipedia.summary(search)
    except DisambiguationError as e:
        await update.message.reply_text(
            "Disambiguated pages found! Adjust your query accordingly.\n<i>{}</i>".format(
                e,
            ),
            parse_mode=ParseMode.HTML,
        )
    except PageError as e:
        await update.message.reply_text(
            "<code>{}</code>".format(e), parse_mode=ParseMode.HTML,
        )
    if res:
        result = f"<b>{search}</b>\n\n"
        result += f"<i>{res}</i>\n"
        result += f"""<a href="https://en.wikipedia.org/wiki/{search.replace(" ", "%20")}">Read more...</a>"""
        if len(result) > 4000:
            with open("result.txt", "w") as f:
                f.write(f"{result}\n\nUwU OwO OmO UmU")
            with open("result.txt", "rb") as f:
                await context.bot.send_document(
                    document=f,
                    filename=f.name,
                    reply_to_message_id=update.message.message_id,
                    chat_id=update.effective_chat.id,
                    parse_mode=ParseMode.HTML,
                )
        else:
            await update.message.reply_text(
                result, parse_mode=ParseMode.HTML, disable_web_page_preview=True,
            )


WIKI_HANDLER = DisableAbleCommandHandler("wiki", wiki, block=False)
application.add_handler(WIKI_HANDLER)
