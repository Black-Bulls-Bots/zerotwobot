import threading

from sqlalchemy import String, Column, Integer, UnicodeText, BigInteger, select

from zerotwobot.modules.sql import SESSION, BASE

DEF_COUNT = 1
DEF_LIMIT = 0
DEF_OBJ = (None, DEF_COUNT, DEF_LIMIT)


class FloodControl(BASE):
    __tablename__ = "antiflood"
    chat_id: str = Column(String(14), primary_key=True)
    user_id:int = Column(BigInteger)
    count: int = Column(Integer, default=DEF_COUNT)
    limit: int = Column(Integer, default=DEF_LIMIT)

    def __init__(self, chat_id):
        self.chat_id = str(chat_id)  # ensure string

    def __repr__(self):
        return "<flood control for %s>" % self.chat_id


class FloodSettings(BASE):
    __tablename__ = "antiflood_settings"
    chat_id: str = Column(String(14), primary_key=True)
    flood_type: int = Column(Integer, default=1)
    value: str = Column(UnicodeText, default="0")

    def __init__(self, chat_id, flood_type=1, value="0"):
        self.chat_id = str(chat_id)
        self.flood_type = flood_type
        self.value = value

    def __repr__(self):
        return "<{} will executing {} for flood.>".format(self.chat_id, self.flood_type)


FloodControl.__table__.create(checkfirst=True)
FloodSettings.__table__.create(checkfirst=True)



CHAT_FLOOD = {}


async def set_flood(chat_id: int | str, amount: int) -> None:
    async with SESSION.begin():
        flood = await SESSION.get(FloodControl, str(chat_id))
        if not flood:
            flood = FloodControl(str(chat_id))

        flood.user_id = None
        flood.limit = amount

        CHAT_FLOOD[str(chat_id)] = (None, DEF_COUNT, amount)

        await SESSION.add(flood)
        await SESSION.commit()


def update_flood(chat_id: str, user_id: int) -> bool:
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


async def get_flood_limit(chat_id: int | str) -> int:
    return await CHAT_FLOOD.get(str(chat_id), DEF_OBJ)[2]


async def set_flood_strength(chat_id: int | str, flood_type: int, value: str) -> None:
    # for flood_type
    # 1 = ban
    # 2 = kick
    # 3 = mute
    # 4 = tban
    # 5 = tmute
    async with SESSION.begin():
        curr_setting = await SESSION.get(FloodSettings, str(chat_id))
        if not curr_setting:
            curr_setting = FloodSettings(
                chat_id,
                flood_type=int(flood_type),
                value=value,
            )

        curr_setting.flood_type = int(flood_type)
        curr_setting.value = str(value)

        await SESSION.add(curr_setting)
        await SESSION.commit()


async def get_flood_setting(chat_id: str) -> tuple[int, str]:
    try:
        setting = await SESSION.get(FloodSettings, str(chat_id))
        if setting:
            return setting.flood_type, setting.value
        else:
            return 1, "0"

    finally:
        await SESSION.close()()


async def migrate_chat(old_chat_id: int | str, new_chat_id: int | str) -> None:
    async with SESSION.begin():
        flood = await SESSION.get(FloodSettings, str(old_chat_id))
        if flood:
            CHAT_FLOOD[str(new_chat_id)] = CHAT_FLOOD.get(str(old_chat_id), DEF_OBJ)
            flood.chat_id = str(new_chat_id)
            await SESSION.commit()

        await SESSION.close()()


async def __load_flood_settings():
    global CHAT_FLOOD
    try:
        all_chats = (await SESSION.scalars(select(FloodControl))).all()
        CHAT_FLOOD = {chat.chat_id: (None, DEF_COUNT, chat.limit) for chat in all_chats}
    finally:
        await SESSION.close()()


__load_flood_settings()
