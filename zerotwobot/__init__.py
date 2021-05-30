import logging
import os
import sys
import time
from dotenv import load_dotenv
import spamwatch
import telegram.ext as tg
from telethon import TelegramClient
from pyrogram import Client
from telegraph import Telegraph


StartTime = time.time()

load_dotenv("config.env")

# enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler("log.txt"), logging.StreamHandler()],
    level=logging.INFO,
)

LOGGER = logging.getLogger(__name__)

# if version < 3.6, stop bot.
if sys.version_info[0] < 3 or sys.version_info[1] < 6:
    LOGGER.error(
        "You MUST have a python version of at least 3.9! Multiple features depend on this. Bot quitting.",
    )
    quit(1)

CONFIG_CHECK = (os.environ.get(
    "___________PLOX_______REMOVE_____THIS_____LINE__________") or None)

if CONFIG_CHECK:
    LOGGER.info(
        "Please remove the line mentioned in the first hashtag from the config.env file"
    )
    quit(1)


TOKEN = os.environ.get("TOKEN") or None
try:
    OWNER_ID = os.environ.get("OWNER_ID")
except ValueError:
    raise Exception("Your OWNER_ID env variable is not a valid integer.")

JOIN_LOGGER = os.environ.get("JOIN_LOGGER") or None
OWNER_USERNAME = os.environ.get("OWNER_USERNAME") or None
PASSWORD = os.environ.get("PASSWORD")

INFOPIC = bool(os.environ.get("INFOPIC") or False) 
EVENT_LOGS = os.environ.get("EVENT_LOGS") or None
WEBHOOK = bool(os.environ.get("WEBHOOK") or False) 
URL = os.environ.get("URL", "")  # Does not contain token
PORT = int(os.environ.get("PORT") or 5000)
CERT_PATH = os.environ.get("CERT_PATH")
API_ID = os.environ.get("API_ID") or None
API_HASH = os.environ.get("API_HASH") or None
DB_URI = os.environ.get("DATABASE_URL")
DONATION_LINK = os.environ.get("DONATION_LINK")
LOAD = os.environ.get("LOAD", "").split()
NO_LOAD = os.environ.get("NO_LOAD", "translation").split()
DEL_CMDS = bool(os.environ.get("DEL_CMDS") or False)
STRICT_GBAN = bool(os.environ.get("STRICT_GBAN") or False)
WORKERS = int(os.environ.get("WORKERS") or 8)
BAN_STICKER = os.environ.get("BAN_STICKER") or "CAADAgADOwADPPEcAXkko5EB3YGYAg"
ALLOW_EXCL = os.environ.get("ALLOW_EXCL") or False
CASH_API_KEY = os.environ.get("CASH_API_KEY") or None
TIME_API_KEY = os.environ.get("TIME_API_KEY") or None
AI_API_KEY = os.environ.get("AI_API_KEY") or None
WALL_API = os.environ.get("WALL_API") or None
SUPPORT_CHAT = os.environ.get("SUPPORT_CHAT") or None
SPAMWATCH_SUPPORT_CHAT = os.environ.get("SPAMWATCH_SUPPORT_CHAT") or None
SPAMWATCH_API = os.environ.get("SPAMWATCH_API") or None

ALLOW_CHATS = os.environ.get("ALLOW_CHATS", True)

try:
    BL_CHATS = set(int(x) for x in os.environ.get("BL_CHATS", "").split())
except ValueError:
    raise Exception("Your blacklisted chats list does not contain valid integers.")

try:
    DRAGONS = set(int(x) for x in os.environ.get("DRAGONS", "").split())
    DEV_USERS = set(int(x) for x in os.environ.get("DEV_USERS", "").split())
except ValueError:
    raise Exception("Your sudo or dev users list does not contain valid integers.")

try:
    DEMONS = set(int(x) for x in os.environ.get("DEMONS", "").split())
except ValueError:
    raise Exception("Your support users list does not contain valid integers.")

try:
    WOLVES = set(int(x) for x in os.environ.get("WOLVES", "").split())
except ValueError:
    raise Exception("Your whitelisted users list does not contain valid integers.")

try:
    TIGERS = set(int(x) for x in os.environ.get("TIGERS", "").split())
except ValueError:
    raise Exception("Your tiger users list does not contain valid integers.")

DRAGONS.add(OWNER_ID)
DEV_USERS.add(OWNER_ID)

if not SPAMWATCH_API:
    sw = None
    LOGGER.warning("SpamWatch API key missing! recheck your ENV variable.")
else:
    try:
        sw = spamwatch.Client(SPAMWATCH_API)
    except:
        sw = None
        LOGGER.warning("Can't connect to SpamWatch!")

updater = tg.Updater(TOKEN, workers=WORKERS, use_context=True)
telethn = TelegramClient("zerotwo", API_ID, API_HASH)
pbot = Client("ZerotwoPyro", api_id=API_ID, api_hash=API_HASH, bot_token=TOKEN)
dispatcher = updater.dispatcher

telegraph = Telegraph()
telegraph.create_account(short_name="zerotwo")

DRAGONS = list(DRAGONS) + list(DEV_USERS)
DEV_USERS = list(DEV_USERS)
WOLVES = list(WOLVES)
DEMONS = list(DEMONS)
TIGERS = list(TIGERS)

# Load at end to ensure all prev variables have been set
from zerotwobot.modules.helper_funcs.handlers import (
    CustomCommandHandler,
    CustomMessageHandler,
    CustomRegexHandler,
)

# make sure the regex handler can take extra kwargs
tg.RegexHandler = CustomRegexHandler
tg.CommandHandler = CustomCommandHandler
tg.MessageHandler = CustomMessageHandler
