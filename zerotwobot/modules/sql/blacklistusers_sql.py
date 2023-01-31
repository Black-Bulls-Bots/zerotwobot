import threading

from zerotwobot.modules.sql import BASE, SESSION
from sqlalchemy import Column, String, UnicodeText


class BlacklistUsers(BASE):
    __tablename__ = "blacklistusers"
    user_id = Column(String(14), primary_key=True)
    reason = Column(UnicodeText)

    def __init__(self, user_id, reason=None):
        self.user_id = user_id
        self.reason = reason


BlacklistUsers.__table__.create(checkfirst=True)

BLACKLIST_USERS = set()


async def blacklist_user(user_id, reason=None):
    async with SESSION.begin():
        user = SESSION.query(BlacklistUsers).get(str(user_id))
        if not user:
            user = BlacklistUsers(str(user_id), reason)
        else:
            user.reason = reason

        await SESSION.add(user)
        await SESSION.commit()
        __load_blacklist_userid_list()


async def unblacklist_user(user_id):
    async with SESSION.begin():
        user = SESSION.query(BlacklistUsers).get(str(user_id))
        if user:
            SESSION.delete(user)

        await SESSION.commit()
        __load_blacklist_userid_list()


async def get_reason(user_id):
    user = SESSION.query(BlacklistUsers).get(str(user_id))
    rep = ""
    if user:
        rep = user.reason

    await SESSION.close()()
    return rep


def is_user_blacklisted(user_id):
    return user_id in BLACKLIST_USERS


async def __load_blacklist_userid_list():
    global BLACKLIST_USERS
    try:
        BLACKLIST_USERS = {int(x.user_id) for x in SESSION.query(BlacklistUsers).all()}
    finally:
        await SESSION.close()()


__load_blacklist_userid_list()
