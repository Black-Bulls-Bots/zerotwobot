import threading

from sqlalchemy import String, Column, Integer, UnicodeText, BigInteger

from zerotwobot.modules.sql import SESSION, BASE

DEF_COUNT = 1
DEF_LIMIT = 0
DEF_OBJ = (None, DEF_COUNT, DEF_LIMIT)


class FloodControl(BASE):
    __tablename__ = "antiflood"
<<<<<<< HEAD
    chat_id = Column(String(14), primary_key=True)
    user_id = Column(BigInteger)
    count = Column(Integer, default=DEF_COUNT)
    limit = Column(Integer, default=DEF_LIMIT)
=======
    chat_id: str = Column(String(14), primary_key=True)
    user_id: int = Column(BigInteger)
    count: int = Column(Integer, default=DEF_COUNT)
    limit: int = Column(Integer, default=DEF_LIMIT)
>>>>>>> 603ab91 (new updates, dropping this repo too.)

    def __init__(self, chat_id):
        self.chat_id = str(chat_id)  # ensure string

    def __repr__(self):
        return "<flood control for %s>" % self.chat_id


class FloodSettings(BASE):
    __tablename__ = "antiflood_settings"
    chat_id = Column(String(14), primary_key=True)
    flood_type = Column(Integer, default=1)
    value = Column(UnicodeText, default="0")

    def __init__(self, chat_id, flood_type=1, value="0"):
        self.chat_id = str(chat_id)
        self.flood_type = flood_type
        self.value = value

    def __repr__(self):
        return "<{} will executing {} for flood.>".format(self.chat_id, self.flood_type)

<<<<<<< HEAD

FloodControl.__table__.create(checkfirst=True)
FloodSettings.__table__.create(checkfirst=True)

INSERTION_FLOOD_LOCK = threading.RLock()
INSERTION_FLOOD_SETTINGS_LOCK = threading.RLock()

CHAT_FLOOD = {}


def set_flood(chat_id, amount):
    with INSERTION_FLOOD_LOCK:
        flood = SESSION.query(FloodControl).get(str(chat_id))
=======
CHAT_FLOOD = {}

async def set_flood(chat_id: int | str, amount: int) -> None:
    "set flood limit for the given chat"
    async with SESSION.begin():
        flood = await SESSION.get(FloodControl, str(chat_id))
>>>>>>> 603ab91 (new updates, dropping this repo too.)
        if not flood:
            flood = FloodControl(str(chat_id))

        flood.user_id = None
        flood.limit = amount

<<<<<<< HEAD
        CHAT_FLOOD[str(chat_id)] = (None, DEF_COUNT, amount)

        SESSION.add(flood)
        SESSION.commit()


def update_flood(chat_id: str, user_id) -> bool:
=======
        await SESSION.add(flood)
        await SESSION.commit()


async def update_flood(chat_id: str, user_id: int) -> bool:
    "update flood limit for the given user in the given chat."
>>>>>>> 603ab91 (new updates, dropping this repo too.)
    if str(chat_id) in CHAT_FLOOD:
        curr_user_id, count, limit = CHAT_FLOOD.get(str(chat_id), DEF_OBJ)

        if limit == 0:  # no antiflood
            return False

        if user_id != curr_user_id or user_id is None:  # other user
            CHAT_FLOOD[str(chat_id)] = (user_id, DEF_COUNT, limit)
            return False

        count += 1
        if count > limit:  # too many msgs, kick
            CHAT_FLOOD[str(chat_id)] = (None, DEF_COUNT, limit)
            return True

        # default -> update
        CHAT_FLOOD[str(chat_id)] = (user_id, count, limit)
        return False


<<<<<<< HEAD
def get_flood_limit(chat_id):
    return CHAT_FLOOD.get(str(chat_id), DEF_OBJ)[2]


def set_flood_strength(chat_id, flood_type, value):
    # for flood_type
    # 1 = ban
    # 2 = kick
    # 3 = mute
    # 4 = tban
    # 5 = tmute
    with INSERTION_FLOOD_SETTINGS_LOCK:
        curr_setting = SESSION.query(FloodSettings).get(str(chat_id))
=======
async def get_flood_limit(chat_id: int | str) -> int:
    "get given chat's flood limit"
    flood = await SESSION.get(FloodControl, str(chat_id))
    if flood:
        return flood.limit
    else:
        return 0

async def set_flood_strength(chat_id: int | str, flood_type: int, value: str) -> None:
    """
    set flood strength for the given chat, check below for flood_types \n
    ```py
    1 = ban
    2 = kick
    3 = mute
    4 = tban
    5 = tmute
    """
    async with SESSION.begin():
        curr_setting = await SESSION.get(FloodSettings, str(chat_id))
>>>>>>> 603ab91 (new updates, dropping this repo too.)
        if not curr_setting:
            curr_setting = FloodSettings(
                chat_id,
                flood_type=int(flood_type),
                value=value,
            )

        curr_setting.flood_type = int(flood_type)
        curr_setting.value = str(value)

        SESSION.add(curr_setting)
        SESSION.commit()


<<<<<<< HEAD
def get_flood_setting(chat_id):
=======
async def get_flood_setting(chat_id: str) -> tuple[int, str]:
    "get given chat's flood settings, returns tuple of flood_type and value"
>>>>>>> 603ab91 (new updates, dropping this repo too.)
    try:
        setting = SESSION.query(FloodSettings).get(str(chat_id))
        if setting:
            return setting.flood_type, setting.value
        else:
            return 1, "0"

    finally:
<<<<<<< HEAD
        SESSION.close()
=======
        await SESSION.close()
>>>>>>> 603ab91 (new updates, dropping this repo too.)


def migrate_chat(old_chat_id, new_chat_id):
    with INSERTION_FLOOD_LOCK:
        flood = SESSION.query(FloodControl).get(str(old_chat_id))
        if flood:
            flood.chat_id = str(new_chat_id)
<<<<<<< HEAD
            SESSION.commit()

        SESSION.close()


def __load_flood_settings():
    global CHAT_FLOOD
    try:
        all_chats = SESSION.query(FloodControl).all()
        CHAT_FLOOD = {chat.chat_id: (None, DEF_COUNT, chat.limit) for chat in all_chats}
    finally:
        SESSION.close()


__load_flood_settings()
=======
            await SESSION.add(flood)
            await SESSION.commit()

        await SESSION.close()
>>>>>>> 603ab91 (new updates, dropping this repo too.)
