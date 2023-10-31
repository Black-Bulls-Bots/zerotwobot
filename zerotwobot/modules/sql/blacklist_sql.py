import threading

from sqlalchemy import func, distinct, Column, String, UnicodeText, Integer

from zerotwobot.modules.sql import SESSION, BASE


class BlackListFilters(BASE):
    __tablename__ = "blacklist"
    chat_id = Column(String(14), primary_key=True)
    trigger = Column(UnicodeText, primary_key=True, nullable=False)

    def __init__(self, chat_id, trigger):
        self.chat_id = str(chat_id)  # ensure string
        self.trigger = trigger

    def __repr__(self):
        return "<Blacklist filter '%s' for %s>" % (self.trigger, self.chat_id)

    def __eq__(self, other):
        return bool(
            isinstance(other, BlackListFilters)
            and self.chat_id == other.chat_id
            and self.trigger == other.trigger,
        )


class BlacklistSettings(BASE):
    __tablename__ = "blacklist_settings"
    chat_id = Column(String(14), primary_key=True)
    blacklist_type = Column(Integer, default=1)
    value = Column(UnicodeText, default="0")

    def __init__(self, chat_id, blacklist_type=1, value="0"):
        self.chat_id = str(chat_id)
        self.blacklist_type = blacklist_type
        self.value = value

    def __repr__(self):
        return "<{} will executing {} for blacklist trigger.>".format(
            self.chat_id,
            self.blacklist_type,
        )


<<<<<<< HEAD
BlackListFilters.__table__.create(checkfirst=True)
BlacklistSettings.__table__.create(checkfirst=True)

BLACKLIST_FILTER_INSERTION_LOCK = threading.RLock()
BLACKLIST_SETTINGS_INSERTION_LOCK = threading.RLock()

CHAT_BLACKLISTS = {}
CHAT_SETTINGS_BLACKLISTS = {}


def add_to_blacklist(chat_id, trigger):
    with BLACKLIST_FILTER_INSERTION_LOCK:
        blacklist_filt = BlackListFilters(str(chat_id), trigger)

        SESSION.merge(blacklist_filt)  # merge to avoid duplicate key issues
        SESSION.commit()
        global CHAT_BLACKLISTS
        if CHAT_BLACKLISTS.get(str(chat_id), set()) == set():
            CHAT_BLACKLISTS[str(chat_id)] = {trigger}
        else:
            CHAT_BLACKLISTS.get(str(chat_id), set()).add(trigger)


def rm_from_blacklist(chat_id, trigger):
    with BLACKLIST_FILTER_INSERTION_LOCK:
        blacklist_filt = SESSION.query(BlackListFilters).get((str(chat_id), trigger))
=======
async def add_to_blacklist(chat_id: int | str, trigger: str) -> None:
    "add the given trigger to chat blacklist"
    async with SESSION.begin():
        blacklist_filt = BlackListFilters(str(chat_id), trigger)

        await SESSION.merge(blacklist_filt)  # merge to avoid duplicate key issues
        await SESSION.commit()


async def rm_from_blacklist(chat_id: int | str, trigger: str) -> bool:
    "remove the given trigger from chat blacklist"
    async with SESSION.begin():
        blacklist_filt = await SESSION.get(BlackListFilters, (str(chat_id), trigger))
>>>>>>> 603ab91 (new updates, dropping this repo too.)
        if blacklist_filt:
            SESSION.delete(blacklist_filt)
            SESSION.commit()
            return True

<<<<<<< HEAD
        SESSION.close()
=======
        await SESSION.close()
>>>>>>> 603ab91 (new updates, dropping this repo too.)
        return False


async def get_chat_blacklist(chat_id: int | str) -> list[str]:
    "return all blacklist triggers for the given chat"
    return (await SESSION.scalars(
        select(BlackListFilters)
        .where(BlackListFilters.chat_id == str(chat_id))
    )).all()


<<<<<<< HEAD
def num_blacklist_filters():
=======
async def num_blacklist_filters() -> int:
    "get the number of blacklist filters overall"
>>>>>>> 603ab91 (new updates, dropping this repo too.)
    try:
        return await SESSION.scalars(select(func.count(BlackListFilters)))
    finally:
<<<<<<< HEAD
        SESSION.close()


def num_blacklist_chat_filters(chat_id):
=======
        await SESSION.close()


async def num_blacklist_chat_filters(chat_id: int | str):
    "return given chat's total number of blacklist triggers"
>>>>>>> 603ab91 (new updates, dropping this repo too.)
    try:
        return (await SESSION.scalars(
            select(BlackListFilters)
            .where(BlackListFilters.chat_id == str(chat_id))
        )).all()
    finally:
<<<<<<< HEAD
        SESSION.close()


def num_blacklist_filter_chats():
=======
        await SESSION.close()


async def num_blacklist_filter_chats() -> int:
    "get number of chats using blacklist feature"
>>>>>>> 603ab91 (new updates, dropping this repo too.)
    try:
        return (await SESSION.scalars(
            select(func.count(BlackListFilters.chat_id.distinct()))
        )).one()
    finally:
        SESSION.close()


<<<<<<< HEAD
def set_blacklist_strength(chat_id, blacklist_type, value):
    # for blacklist_type
    # 0 = nothing
    # 1 = delete
    # 2 = warn
    # 3 = mute
    # 4 = kick
    # 5 = ban
    # 6 = tban
    # 7 = tmute
    with BLACKLIST_SETTINGS_INSERTION_LOCK:
        global CHAT_SETTINGS_BLACKLISTS
        curr_setting = SESSION.query(BlacklistSettings).get(str(chat_id))
=======
async def set_blacklist_strength(chat_id: int | str, blacklist_type: int, value: str) -> None:
    """
    set blacklist strength for the given chat, refer below for available types
    ```py
    0 = nothing
    1 = delete
    2 = warn
    3 = mute
    4 = kick
    5 = ban
    6 = tban
    7 = tmute
    """
    async with SESSION.begin():
        curr_setting = await SESSION.get(BlacklistSettings, str(chat_id))
>>>>>>> 603ab91 (new updates, dropping this repo too.)
        if not curr_setting:
            curr_setting = BlacklistSettings(
                chat_id,
                blacklist_type=blacklist_type,
                value=value,
            )

        curr_setting.blacklist_type = blacklist_type
        curr_setting.value = str(value)

        SESSION.add(curr_setting)
        SESSION.commit()


<<<<<<< HEAD
def get_blacklist_setting(chat_id):
=======
async def get_blacklist_setting(chat_id: int | str) -> tuple[int, str]:
    "get blacklist settings for the given chat"
>>>>>>> 603ab91 (new updates, dropping this repo too.)
    try:
        setting = await SESSION.get(BlacklistSettings, str(chat_id))
        if setting:
            return setting.blacklist_type, setting.value
        else:
            return 1, "0"

    finally:
<<<<<<< HEAD
        SESSION.close()


def __load_chat_blacklists():
    global CHAT_BLACKLISTS
    try:
        chats = SESSION.query(BlackListFilters.chat_id).distinct().all()
        for (chat_id,) in chats:  # remove tuple by ( ,)
            CHAT_BLACKLISTS[chat_id] = []

        all_filters = SESSION.query(BlackListFilters).all()
        for x in all_filters:
            CHAT_BLACKLISTS[x.chat_id] += [x.trigger]

        CHAT_BLACKLISTS = {x: set(y) for x, y in CHAT_BLACKLISTS.items()}

    finally:
        SESSION.close()


def __load_chat_settings_blacklists():
    global CHAT_SETTINGS_BLACKLISTS
    try:
        chats_settings = SESSION.query(BlacklistSettings).all()
        for x in chats_settings:  # remove tuple by ( ,)
            CHAT_SETTINGS_BLACKLISTS[x.chat_id] = {
                "blacklist_type": x.blacklist_type,
                "value": x.value,
            }

    finally:
        SESSION.close()

=======
        await SESSION.close()


>>>>>>> 603ab91 (new updates, dropping this repo too.)

def migrate_chat(old_chat_id, new_chat_id):
    with BLACKLIST_FILTER_INSERTION_LOCK:
        chat_filters = (
            SESSION.query(BlackListFilters)
            .filter(BlackListFilters.chat_id == str(old_chat_id))
            .all()
        )
        for filt in chat_filters:
            filt.chat_id = str(new_chat_id)
<<<<<<< HEAD
        SESSION.commit()


__load_chat_blacklists()
__load_chat_settings_blacklists()
=======
        await SESSION.commit()
>>>>>>> 603ab91 (new updates, dropping this repo too.)
