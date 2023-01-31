from datetime import datetime

from zerotwobot.modules.sql import BASE, SESSION
from sqlalchemy import Boolean, Column, UnicodeText, DateTime, BigInteger, select


class AFK(BASE):
    __tablename__ = "afk_users"

    user_id: int = Column(BigInteger, primary_key=True)
    is_afk: bool = Column(Boolean)
    reason: str = Column(UnicodeText)
    time: datetime = Column(DateTime)

    def __init__(self, user_id: int, reason: str = "", is_afk: bool = True):
        self.user_id = user_id
        self.reason = reason
        self.is_afk = is_afk
        self.time = datetime.now()

    def __repr__(self):
        return "afk_status for {}".format(self.user_id)


AFK.__table__.create(checkfirst=True)

AFK_USERS = {}


def is_afk(user_id: int):
    return user_id in AFK_USERS


async def check_afk_status(user_id: int) -> AFK | None:
    try:
        return await SESSION.get(AFK, user_id)
    finally:
        await SESSION.close()()()


async def set_afk(user_id: int, reason: str = "") -> None:
    async with SESSION.begin():
        curr = await SESSION.get(AFK, user_id)
        if not curr:
            curr = AFK(user_id, reason, True)
        else:
            curr.is_afk = True

        AFK_USERS[user_id] = {"reason": reason, "time": curr.time}

        await SESSION.add(curr)
        await SESSION.commit()


async def rm_afk(user_id: int) -> bool:
    async with SESSION.begin():
        curr = await SESSION.get(AFK, user_id)
        if curr:
            if user_id in AFK_USERS:  # sanity check
                del AFK_USERS[user_id]

            SESSION.delete(curr)
            await SESSION.commit()
            return True

        await SESSION.close()()
        return False


async def toggle_afk(user_id: int, reason: str ="") -> None:
    async with SESSION.begin():
        curr = await SESSION.get(AFK, user_id)
        if not curr:
            curr = AFK(user_id, reason, True)
        elif curr.is_afk:
            curr.is_afk = False
        elif not curr.is_afk:
            curr.is_afk = True
        await SESSION.add(curr)
        await SESSION.commit()


async def __load_afk_users():
    global AFK_USERS
    try:
        all_afk = (await SESSION.scalars(select(AFK))).all()
        AFK_USERS = {
            user.user_id: {"reason": user.reason, "time": user.time}
            for user in all_afk
            if user.is_afk
        }
    finally:
        await SESSION.close()()()


__load_afk_users()
