from emoji import UNICODE_EMOJI
from googletrans import LANGUAGES, Translator
from telegram import ParseMode, Update
from telegram.ext import CallbackContext

from zerotwobot import dispatcher
from zerotwobot.modules.disable import DisableAbleCommandHandler



def totranslate(update: Update, context: CallbackContext):
    message = update.effective_message
    problem_lang_code = []
    for key in LANGUAGES:
        if "-" in key:
            problem_lang_code.append(key)

    try:
        if message.reply_to_message:
            args = update.effective_message.text.split(None, 1)
            if message.reply_to_message.text:
                text = message.reply_to_message.text
            elif message.reply_to_message.caption:
                text = message.reply_to_message.caption

            try:
                source_lang = args[1].split(None, 1)[0]
            except (IndexError, AttributeError):
                source_lang = "en"

        else:
            args = update.effective_message.text.split(None, 2)
            text = args[2]
            source_lang = args[1]

        if source_lang.count("-") == 2:
            for lang in problem_lang_code:
                if lang in source_lang:
                    if source_lang.startswith(lang):
                        dest_lang = source_lang.rsplit("-", 1)[1]
                        source_lang = source_lang.rsplit("-", 1)[0]
                    else:
                        dest_lang = source_lang.split("-", 1)[1]
                        source_lang = source_lang.split("-", 1)[0]
        elif source_lang.count("-") == 1:
            for lang in problem_lang_code:
                if lang in source_lang:
                    dest_lang = source_lang
                    source_lang = None
                    break
            if dest_lang is None:
                dest_lang = source_lang.split("-")[1]
                source_lang = source_lang.split("-")[0]
        else:
            dest_lang = source_lang
            source_lang = None

        exclude_list = UNICODE_EMOJI.keys()
        for emoji in exclude_list:
            if emoji in text:
                text = text.replace(emoji, "")

        trl = Translator()
        if source_lang is None:
            detection = trl.detect(text)
            trans_str = trl.translate(text, dest=dest_lang)
            return message.reply_text(
                f"Translated from `{detection.lang}` to `{dest_lang}`:\n`{trans_str.text}`",
                parse_mode=ParseMode.MARKDOWN,
            )
        else:
            trans_str = trl.translate(text, dest=dest_lang, src=source_lang)
            message.reply_text(
                f"Translated from `{source_lang}` to `{dest_lang}`:\n`{trans_str.text}`",
                parse_mode=ParseMode.MARKDOWN,
            )

    except IndexError:
        update.effective_message.reply_text(
            "Reply to messages or write messages from other languages ​​for translating into the intended language\n\n"
            "Example: `/tr en-ta` to translate from English to Tamil\n"
            "Or use: `/tr ta` for automatic detection and translating it into Tamil.\n"
            "See [List of Language Codes](https://t.me/blackbull_bots/15) for a list of language codes.",
            parse_mode="markdown",
            disable_web_page_preview=True,
        )
    except ValueError:
        update.effective_message.reply_text("The intended language is not found!")
    else:
        return


__help__ = """
• `/tr` or `/tl` (language code) as reply to a long message
*Example:*
  `/tr en`*:* translates something to english
  `/tr hi-en`*:* translates hindi to english
"""

TRANSLATE_HANDLER = DisableAbleCommandHandler(["tr", "tl"], totranslate, run_async=True)

dispatcher.add_handler(TRANSLATE_HANDLER)

__mod_name__ = "Translator"
__command_list__ = ["tr", "tl"]
__handlers__ = [TRANSLATE_HANDLER]
