import subprocess
import os
from zerotwobot import LOGGER, application
from zerotwobot.modules.helper_funcs.chat_status import check_admin
from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import ContextTypes, CommandHandler

@check_admin(only_dev=True)
async def shell(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.effective_message
    chat = update.effective_chat
    cmd = message.text.split(" ", 1)
    if len(cmd) == 1:
        await message.reply_text("No command to execute was given.")
        return
    cmd = cmd[1]
    process = subprocess.Popen(
        cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True,
    )
    stdout, stderr = process.communicate()
    reply = ""
    stderr = stderr.decode()
    stdout = stdout.decode()
    if stdout:
        reply += f"*Stdout*\n`{stdout}`\n"
        LOGGER.info(f"Shell - {cmd} - {stdout}")
    if stderr:
        reply += f"*Stderr*\n`{stderr}`\n"
        LOGGER.error(f"Shell - {cmd} - {stderr}")
    if len(reply) > 3000:
        with open("shell_output.txt", "w") as file:
            file.write(reply)
        with open("shell_output.txt", "rb") as doc:
            await context.bot.send_document(
                document=doc,
                filename=doc.name,
                reply_to_message_id=message.message_id,
                chat_id=message.chat_id,
                message_thread_id=message.message_thread_id if chat.is_forum else None
            )
        
        if os.path.isfile("shell_ouput.txt"):
            os.remove("shell_output.txt")
    else:
        await message.reply_text(reply, parse_mode=ParseMode.MARKDOWN)


SHELL_HANDLER = CommandHandler(["sh"], shell, block=False)
application.add_handler(SHELL_HANDLER)
__mod_name__ = "Shell"
__command_list__ = ["sh"]
__handlers__ = [SHELL_HANDLER]
