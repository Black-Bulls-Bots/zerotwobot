import os
from datetime import datetime
from telethon import events

from PIL import Image
from telegraph import Telegraph, exceptions, upload_file

from zerotwobot import telethn, TEMP_DOWNLOAD_LOC


telegraph = Telegraph()
r = telegraph.create_account(short_name="ZeroTwo")
auth_url = r["auth_url"]


async def telegraph(event):
    if not os.path.isdir(TEMP_DOWNLOAD_LOC):
        os.mkdir(TEMP_DOWNLOAD_LOC)

    optional_title = event.pattern_match.group(2)
    if event.reply_to_msg_id:
        start = datetime.now()
        r_message = await event.get_reply_message()
        input_str = event.pattern_match.group(1)
        if input_str == "m":
            f_name = await telethn.download_media(
                r_message, TEMP_DOWNLOAD_LOC
            )
            end = datetime.now()
            ms = (end - start).seconds
            h = await event.reply(
                "Downloaded to {} in {} seconds.".format(f_name, ms)
            )
            if f_name.endswith((".webp")):
                im = Image.open(f_name)
                im.save(f_name, "PNG")
            try:
                start = datetime.now()
                media_urls = upload_file(f_name)
            except exceptions.TelegraphException as exc:
                os.remove(f_name)
                return await h.edit("ERROR: " + str(exc))
            os.remove(f_name)
            await h.edit(f"Uploaded to https://te.legra.ph{media_urls[0]})", link_preview=True)

        elif input_str == "t":
            user_object = await telethn.get_entity(r_message.sender_id)
            title_of_page = user_object.first_name + " " + (user_object.last_name or "")
            if optional_title:
                title_of_page = optional_title
            page_content = r_message.message
            if r_message.media:
                if page_content != "":
                    title_of_page = page_content
                f_name = await telethn.download_media(r_message, TEMP_DOWNLOAD_LOC)
                m_list = None
                with open(f_name, "rb") as fd:
                    m_list = fd.readlines()
                for m in m_list:
                    page_content += m.decode("UTF-8") + "\n"
                os.remove(f_name)
            page_content = page_content.replace("\n", "<br>")
            response = telegraph.create_page(title_of_page, html_content=page_content)
            end = datetime.now()
            ms = (end - start).seconds
            await event.reply(f"Pasted to https://te.legra.ph/{response["path"]} in {ms} seconds.", link_preview=True)
    else:
        await event.reply("Reply to a message to get a permanent te.legra.ph link.")


__help__ = """
I can upload files to Telegraph

 ❍ /tgm :Get Telegraph Link Of Replied Media
 ❍ /tgt :Get Telegraph Link of Replied Text
 ❍ /tgt [custom name]: Get telegraph link of replied text with custom name.
"""

TELEGRAPH_HANDLER = telegraph, events.NewMessage(pattern="^/tg(m|t) ?(.*)")

telethn.add_event_handler(*TELEGRAPH_HANDLER)

__mod_name__ = "Telegraph"
__command_list__ = ["tgm", "tgt"]
__handlers__ = [TELEGRAPH_HANDLER]
