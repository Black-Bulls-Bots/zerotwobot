import datetime
import html
import textwrap

import bs4
import jikanpy
from httpx import AsyncClient
from zerotwobot import application
from zerotwobot.modules.disable import DisableAbleCommandHandler
from zerotwobot.modules.helper_funcs.string_handling import (
    markdown_parser,
    markdown_to_html,
)
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update, Message
from telegram.ext import ContextTypes
from telegram.constants import ParseMode

info_btn = "More Information"
kaizoku_btn = "Kaizoku ☠️"
kayo_btn = "Kayo 🏴‍☠️"
prequel_btn = "⬅️ Prequel"
sequel_btn = "Sequel ➡️"
close_btn = "Close ❌"


def shorten(description, info="anilist.co"):
    msg = ""
    if len(description) > 700:
        description = description[0:500] + "...."
        msg += f"\n*Description*: {description} [Read More]({info})"
    else:
        msg += f"\n*Description*:{description}"
    return msg


# time formatter from uniborg
def t(milliseconds: int) -> str:
    """Inputs time in milliseconds, to get beautified time,
    as string"""
    seconds, milliseconds = divmod(int(milliseconds), 1000)
    minutes, seconds = divmod(seconds, 60)
    hours, minutes = divmod(minutes, 60)
    days, hours = divmod(hours, 24)
    tmp = (
        ((str(days) + " Days, ") if days else "")
        + ((str(hours) + " Hours, ") if hours else "")
        + ((str(minutes) + " Minutes, ") if minutes else "")
        + ((str(seconds) + " Seconds, ") if seconds else "")
        + ((str(milliseconds) + " ms, ") if milliseconds else "")
    )
    return tmp[:-2]


airing_query = """
query ($id: Int,$search: String) {
    Media (id: $id, type: ANIME,search: $search) {
        id
        episodes
        title {
            romaji
            english
            native
        }
        nextAiringEpisode {
            airingAt
            timeUntilAiring
            episode
        }
    }
}
"""

fav_query = """
query ($id: Int) {
    Media (id: $id, type: ANIME) {
        id
        title {
            romaji
            english
            native
        }
    }
}
"""

anime_query = """
query ($id: Int,$search: String) {
    Media (id: $id, type: ANIME,search: $search) {
        id
        title {
            romaji
            english
            native
        }
        description (asHtml: false)
        startDate{
            year
        }
        episodes
        season
        type
        format
        isAdult
        status
        duration
        siteUrl
        studios{
            nodes{
                name
            }
        }
        trailer{
            id
            site
            thumbnail
        }
        averageScore
        genres
        bannerImage
    }
}
"""

character_query = """
query ($query: String) {
    Character (search: $query) {
        id
        name {
            first
            last
            full
        }
        siteUrl
        gender
        image {
            large
        }
        description (asHtml : true)
    }
}
"""

manga_query = """
query ($id: Int,$search: String) {
    Media (id: $id, type: MANGA,search: $search) {
        id
        title {
            romaji
            english
            native
        }
        description (asHtml: false)
        startDate{
            year
        }
        type
        format
        status
        siteUrl
        averageScore
        genres
        bannerImage
    }
}
"""

url = "https://graphql.anilist.co"


async def extract_arg(message: Message):
    split = message.text.split(" ", 1)
    if len(split) > 1:
        return split[1]
    reply = message.reply_to_message
    if reply is not None and not reply.forum_topic_created:
        return reply.text
    return None


async def airing(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.effective_message
    search_str = await extract_arg(message)
    if not search_str:
        await update.effective_message.reply_text(
            "Tell Anime Name :) ( /airing <anime name>)",
        )
        return
    variables = {"search": search_str}
    async with AsyncClient() as client:
        r = await client.post(
            url,
            json={"query": airing_query, "variables": variables},
        )
    if not r.status_code in [401, 404, 500, 503]:
        response = r.json()["data"]["Media"]
    else:
        await update.effective_message.reply_text("Umm that didn't work!")
        return
    msg = f"*Name*: *{response['title']['romaji']}*(`{response['title']['native']}`)\n*ID*: `{response['id']}`"
    if response["nextAiringEpisode"]:
        time = response["nextAiringEpisode"]["timeUntilAiring"] * 1000
        time = t(time)
        msg += f"\n*Episode*: `{response['nextAiringEpisode']['episode']}`\n*Airing In*: `{time}`"
    else:
        msg += f"\n*Episode*:{response['episodes']}\n*Status*: `N/A`"
    await update.effective_message.reply_text(msg, parse_mode=ParseMode.MARKDOWN)


async def anime(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.effective_message
    search = await extract_arg(message)
    if not search:
        await update.effective_message.reply_text("Format : /anime < anime name >")
        return
    variables = {"search": search}
    async with AsyncClient() as client:
        r = await client.post(
            url,
            json={"query": anime_query, "variables": variables},
        )
    json = r.json()
    if "errors" in json.keys():
        await update.effective_message.reply_text("Anime not found")
        return
    if json:
        json = json["data"]["Media"]
        msg = f"*{json['title']['romaji']}*(`{json['title']['native']}`)\n\n➢ *Type*: {json['format']}\n➢ *Status*: {json['status']}\n➢ *Episodes*: {json.get('episodes', 'N/A')}\n➢ *Duration*: {json.get('duration', 'N/A')} Per Ep.\n➢ *Score*: {json['averageScore']}\n➢ *Genres*: `"
        for x in json["genres"]:
            msg += f"{x}, "
        msg = msg[:-2] + "`\n"
        msg += "➢ *Adult*: True 🔞 \n" if json["isAdult"] else "➢ *Adult*: False\n"
        msg += "➢ *Studios*: `"
        for x in json["studios"]["nodes"]:
            msg += f"{x['name']}, "
        msg = msg[:-2] + "`\n"
        info = json.get("siteUrl")
        trailer = json.get("trailer", None)
        anime_id = json["id"]
        if trailer:
            trailer_id = trailer.get("id", None)
            site = trailer.get("site", None)
            if site == "youtube":
                trailer = "https://youtu.be/" + trailer_id
        description = (
            json.get("description", "N/A")
            .replace("<i>", "")
            .replace("</i>", "")
            .replace("<br>", "")
        )
        msg += shorten(description, info)
        image = f"https://img.anili.st/media/{anime_id}"
        if trailer:
            buttons = [
                [
                    InlineKeyboardButton("More Info", url=info),
                    InlineKeyboardButton("Trailer 🎬", url=trailer),
                ],
            ]
        else:
            buttons = [[InlineKeyboardButton("More Info", url=info)]]
        if image:
            try:
                await update.effective_message.reply_photo(
                    photo=image,
                    caption=msg,
                    parse_mode=ParseMode.MARKDOWN,
                    reply_markup=InlineKeyboardMarkup(buttons),
                )
            except:
                msg += f" [〽️]({image})"
                await update.effective_message.reply_text(
                    msg,
                    parse_mode=ParseMode.MARKDOWN,
                    reply_markup=InlineKeyboardMarkup(buttons),
                )
        else:
            await update.effective_message.reply_text(
                msg,
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=InlineKeyboardMarkup(buttons),
            )


async def character(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.effective_message
    search = await extract_arg(message)
    if not search:
        await update.effective_message.reply_text(
            "Format : /character < character name >"
        )
        return
    variables = {"query": search}
    async with AsyncClient() as client:
        r = await client.post(
            url,
            json={"query": character_query, "variables": variables},
        )
    json = r.json()
    if "errors" in json.keys():
        await update.effective_message.reply_text("Character not found")
        return
    if json:
        json = json["data"]["Character"]
        msg = f"*{json.get('name').get('full')}*(`{json.get('name').get('native')}`)\n"
        msg += f"*Gender*: {json.get('gender', 'N/A')}\n"
        description = f"{json['description']}"
        site_url = json.get("siteUrl")
        msg += shorten(description, site_url)
        image = json.get("image", None)
        if image:
            image = image.get("large")
            await update.effective_message.reply_photo(
                photo=image,
                caption=markdown_to_html(markdown_parser(msg)),
                parse_mode=ParseMode.HTML,
            )
        else:
            await update.effective_message.reply_text(
                markdown_to_html(markdown_parser(msg)),
                parse_mode=ParseMode.HTML,
            )


async def manga(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.effective_message
    search = await extract_arg(message)
    if not search:
        await update.effective_message.reply_text("Format : /manga < manga name >")
        return
    variables = {"search": search}
    async with AsyncClient() as client:
        r = await client.post(
            url,
            json={"query": manga_query, "variables": variables},
        )
    json = r.json()
    msg = ""
    if "errors" in json.keys():
        await update.effective_message.reply_text("Manga not found")
        return
    if json:
        json = json["data"]["Media"]
        title, title_native = json["title"].get("romaji", False), json["title"].get(
            "native",
            False,
        )
        start_date, status, score = (
            json["startDate"].get("year", False),
            json.get("status", False),
            json.get("averageScore", False),
        )
        if title:
            msg += f"*{title}*"
            if title_native:
                msg += f"(`{title_native}`)"
        if start_date:
            msg += f"\n\n➢ *Start Date* - `{start_date}`"
        if status:
            msg += f"\n➢ *Status* - `{status}`"
        if score:
            msg += f"\n➢ *Score* - `{score}`"
        msg += "\n➢ *Genres* - "
        for x in json.get("genres", []):
            msg += f"{x}, "
        msg = msg[:-2]
        info = json["siteUrl"]
        buttons = [[InlineKeyboardButton("More Info", url=info)]]
        image = f"https://img.anili.st/media/{json['id']}"
        msg += f"\n➢ *Description* - _{json.get('description', None)}_"
        if image:
            try:
                await update.effective_message.reply_photo(
                    photo=image,
                    caption=msg,
                    parse_mode=ParseMode.MARKDOWN,
                    reply_markup=InlineKeyboardMarkup(buttons),
                )
            except:
                msg += f" [〽️]({image})"
                await update.effective_message.reply_text(
                    msg,
                    parse_mode=ParseMode.MARKDOWN,
                    reply_markup=InlineKeyboardMarkup(buttons),
                )
        else:
            await update.effective_message.reply_text(
                msg,
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=InlineKeyboardMarkup(buttons),
            )


async def user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.effective_message
    search_query = await extract_arg(message)

    if not search_query:
        await update.effective_message.reply_text("Format : /user <username>")
        return

    jikan = jikanpy.jikan.Jikan()

    try:
        us = jikan.user(search_query)
    except jikanpy.APIException:
        await update.effective_message.reply_text("Username not found.")
        return

    progress_message = await update.effective_message.reply_text("Searching.... ")

    date_format = "%Y-%m-%d"
    if us["image_url"] is None:
        img = "https://cdn.myanimelist.net/images/questionmark_50.gif"
    else:
        img = us["image_url"]

    try:
        user_birthday = datetime.datetime.fromisoformat(us["birthday"])
        user_birthday_formatted = user_birthday.strftime(date_format)
    except:
        user_birthday_formatted = "Unknown"

    user_joined_date = datetime.datetime.fromisoformat(us["joined"])
    user_joined_date_formatted = user_joined_date.strftime(date_format)

    for entity in us:
        if us[entity] is None:
            us[entity] = "Unknown"

    about = us["about"].split(" ", 60)

    try:
        about.pop(60)
    except IndexError:
        pass

    about_string = " ".join(about)
    about_string = about_string.replace("<br>", "").strip().replace("\r\n", "\n")

    caption = ""

    caption += textwrap.dedent(
        f"""
    *Username*: [{us['username']}]({us['url']})

    *Gender*: `{us['gender']}`
    *Birthday*: `{user_birthday_formatted}`
    *Joined*: `{user_joined_date_formatted}`
    *Days wasted watching anime*: `{us['anime_stats']['days_watched']}`
    *Days wasted reading manga*: `{us['manga_stats']['days_read']}`

    """,
    )

    caption += f"*About*: {about_string}"

    buttons = [
        [InlineKeyboardButton(info_btn, url=us["url"])],
        [
            InlineKeyboardButton(
                close_btn,
                callback_data=f"anime_close, {message.from_user.id}",
            ),
        ],
    ]

    await update.effective_message.reply_photo(
        photo=img,
        caption=caption,
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=InlineKeyboardMarkup(buttons),
        disable_web_page_preview=False,
    )
    await progress_message.delete()


async def upcoming(update: Update, context: ContextTypes.DEFAULT_TYPE):
    jikan = jikanpy.jikan.Jikan()
    upcomin = jikan.top("anime", page=1, subtype="upcoming")

    upcoming_list = [entry["title"] for entry in upcomin["top"]]
    upcoming_message = ""

    for entry_num in range(len(upcoming_list)):
        if entry_num == 10:
            break
        upcoming_message += f"{entry_num + 1}. {upcoming_list[entry_num]}\n"

    await update.effective_message.reply_text(upcoming_message)


async def site_search(update: Update, context: ContextTypes.DEFAULT_TYPE, site: str):
    message = update.effective_message
    search_query = await extract_arg(message)
    more_results = True

    if not search_query:
        await message.reply_text("Give something to search")
        return

    if site == "kaizoku":
        search_url = f"https://animekaizoku.com/?s={search_query}"
        async with AsyncClient() as client:
            r = await client.get(search_url)
        html_text = r.text
        soup = bs4.BeautifulSoup(html_text, "html.parser")
        search_result = soup.find_all("h2", {"class": "post-title"})

        if search_result:
            result = f"<b>Search results for</b> <code>{html.escape(search_query)}</code> <b>on</b> @KaizokuAnime: \n"
            for entry in search_result:
                post_link = "https://animekaizoku.com/" + entry.a["href"]
                post_name = html.escape(entry.text)
                result += f"• <a href='{post_link}'>{post_name}</a>\n"
        else:
            more_results = False
            result = f"<b>No result found for</b> <code>{html.escape(search_query)}</code> <b>on</b> @KaizokuAnime"

    elif site == "kayo":
        search_url = f"https://animekayo.com/?s={search_query}"
        async with AsyncClient() as client:
            r = await client.get(search_url)
        html_text = r.text
        soup = bs4.BeautifulSoup(html_text, "html.parser")
        search_result = soup.find_all("h2", {"class": "title"})

        result = f"<b>Search results for</b> <code>{html.escape(search_query)}</code> <b>on</b> @KayoAnime: \n"
        for entry in search_result:

            if entry.text.strip() == "Nothing Found":
                result = f"<b>No result found for</b> <code>{html.escape(search_query)}</code> <b>on</b> @KayoAnime"
                more_results = False
                break

            post_link = entry.a["href"]
            post_name = html.escape(entry.text.strip())
            result += f"• <a href='{post_link}'>{post_name}</a>\n"

    buttons = [[InlineKeyboardButton("See all results", url=search_url)]]

    if more_results:
        await message.reply_text(
            result,
            parse_mode=ParseMode.HTML,
            reply_markup=InlineKeyboardMarkup(buttons),
            disable_web_page_preview=True,
        )
    else:
        await message.reply_text(
            result,
            parse_mode=ParseMode.HTML,
            disable_web_page_preview=True,
        )


async def kaizoku(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await site_search(update, context, "kaizoku")


async def kayo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await site_search(update, context, "kayo")


__help__ = """
Get information about anime, manga or characters from [AniList](anilist.co).

*Available commands:*

 • `/anime <anime>`*:* returns information about the anime.
 • `/character <character>`*:* returns information about the character.
 • `/manga <manga>`*:* returns information about the manga.
 • `/user <user>`*:* returns information about a MyAnimeList user.
 • `/upcoming`*:* returns a list of new anime in the upcoming seasons.
 • `/kaizoku <anime>`*:* search an anime on animekaizoku.com
 • `/kayo <anime>`*:* search an anime on animekayo.com
 • `/airing <anime>`*:* returns anime airing info.

 """

ANIME_HANDLER = DisableAbleCommandHandler("anime", anime, block=False)
AIRING_HANDLER = DisableAbleCommandHandler("airing", airing, block=False)
CHARACTER_HANDLER = DisableAbleCommandHandler("character", character, block=False)
MANGA_HANDLER = DisableAbleCommandHandler("manga", manga, block=False)
USER_HANDLER = DisableAbleCommandHandler("user", user, block=False)
UPCOMING_HANDLER = DisableAbleCommandHandler("upcoming", upcoming, block=False)
KAIZOKU_SEARCH_HANDLER = DisableAbleCommandHandler("kaizoku", kaizoku, block=False)
KAYO_SEARCH_HANDLER = DisableAbleCommandHandler("kayo", kayo, block=False)

application.add_handler(ANIME_HANDLER)
application.add_handler(CHARACTER_HANDLER)
application.add_handler(MANGA_HANDLER)
application.add_handler(AIRING_HANDLER)
application.add_handler(USER_HANDLER)
application.add_handler(KAIZOKU_SEARCH_HANDLER)
application.add_handler(KAYO_SEARCH_HANDLER)
application.add_handler(UPCOMING_HANDLER)

__mod_name__ = "Anime"
__command_list__ = [
    "anime",
    "manga",
    "character",
    "user",
    "upcoming",
    "kaizoku",
    "airing",
    "kayo",
]
__handlers__ = [
    ANIME_HANDLER,
    CHARACTER_HANDLER,
    MANGA_HANDLER,
    USER_HANDLER,
    UPCOMING_HANDLER,
    KAIZOKU_SEARCH_HANDLER,
    KAYO_SEARCH_HANDLER,
    AIRING_HANDLER,
]
