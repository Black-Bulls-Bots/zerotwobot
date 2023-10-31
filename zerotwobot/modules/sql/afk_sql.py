import threading

from datetime import datetime

from zerotwobot.modules.sql import BASE, SESSION
from sqlalchemy import Boolean, Column, UnicodeText, DateTime, BigInteger
from sqlalchemy.orm import Mapped, mapped_column


class AFK(BASE):
    __tablename__ = "afk_users"

    user_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
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

async def is_afk(user_id: int) -> bool:
    user = await SESSION.get(AFK, user_id)
    if user is not None and user.is_afk:
        return True
    else:
        return False


async def check_afk_status(user_id: int) -> AFK | None:
    "check if the given user is afk else returns None"
    try:
        return SESSION.query(AFK).get(user_id)
    finally:
        await SESSION.close()


async def set_afk(user_id: int, reason: str = "") -> None:
    "set afk for the given user to true."
    async with SESSION.begin():
        curr = await SESSION.get(AFK, user_id)
        if not curr:
            curr = AFK(user_id, reason, True)
        else:
            curr.is_afk = True

        await SESSION.add(curr)
        await SESSION.commit()


async def rm_afk(user_id: int) -> bool:
    "remove given user from afk."
    async with SESSION.begin():
        curr = await SESSION.get(AFK, user_id)
        if curr:
            SESSION.delete(curr)
            SESSION.commit()
            return True

        await SESSION.close()
        return False

