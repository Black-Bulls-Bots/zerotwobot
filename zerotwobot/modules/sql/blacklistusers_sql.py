import threading

from zerotwobot.modules.sql import BASE, SESSION
from sqlalchemy import Column, String, UnicodeText, select


class BlacklistUsers(BASE):
    __tablename__ = "blacklistusers"
    user_id: str = Column(String(14), primary_key=True)
    reason: str = Column(UnicodeText)

    def __init__(self, user_id, reason=None):
        self.user_id = user_id
        self.reason = reason


<<<<<<< HEAD
BlacklistUsers.__table__.create(checkfirst=True)

BLACKLIST_LOCK = threading.RLock()
BLACKLIST_USERS = set()


def blacklist_user(user_id, reason=None):
    with BLACKLIST_LOCK:
        user = SESSION.query(BlacklistUsers).get(str(user_id))
=======
async def blacklist_user(user_id: int | str, reason: str = None) -> None:
    "Blacklist a given user"
    async with SESSION.begin():
        user = await SESSION.get(BlacklistUsers, str(user_id))
>>>>>>> 603ab91 (new updates, dropping this repo too.)
        if not user:
            user = BlacklistUsers(str(user_id), reason)
        else:
            user.reason = reason

<<<<<<< HEAD
        SESSION.add(user)
        SESSION.commit()
        __load_blacklist_userid_list()


def unblacklist_user(user_id):
    with BLACKLIST_LOCK:
        user = SESSION.query(BlacklistUsers).get(str(user_id))
        if user:
            SESSION.delete(user)

        SESSION.commit()
        __load_blacklist_userid_list()


def get_reason(user_id):
    user = SESSION.query(BlacklistUsers).get(str(user_id))
=======
        await SESSION.add(user)
        await SESSION.commit()


async def unblacklist_user(user_id: int | str) -> None:
    "Unblacklist a given user"
    async with SESSION.begin():
        user = await SESSION.get(BlacklistUsers, str(user_id))
        if user:
            SESSION.delete(user)

        await SESSION.commit()


async def get_reason(user_id: int | str) -> str:
    "get blacklist reason for the given user"
    user = SESSION.get(BlacklistUsers, str(user_id))
>>>>>>> 603ab91 (new updates, dropping this repo too.)
    rep = ""
    if user:
        rep = user.reason

<<<<<<< HEAD
    SESSION.close()
=======
    await SESSION.close()
>>>>>>> 603ab91 (new updates, dropping this repo too.)
    return rep


async def is_user_blacklisted(user_id):
    return await SESSION.execute(
        select(BlacklistUsers)
        .where(BlacklistUsers.user_id == user_id)
    )

<<<<<<< HEAD

def __load_blacklist_userid_list():
    global BLACKLIST_USERS
    try:
        BLACKLIST_USERS = {int(x.user_id) for x in SESSION.query(BlacklistUsers).all()}
    finally:
        SESSION.close()


__load_blacklist_userid_list()
=======
>>>>>>> 603ab91 (new updates, dropping this repo too.)
