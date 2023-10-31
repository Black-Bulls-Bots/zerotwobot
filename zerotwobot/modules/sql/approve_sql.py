import threading

from sqlalchemy import Column, String, Integer, BigInteger

from zerotwobot.modules.sql import BASE, SESSION


class Approvals(BASE):
    __tablename__ = "approval"
    chat_id = Column(String(14), primary_key=True)
    user_id = Column(BigInteger, primary_key=True)

    def __init__(self, chat_id, user_id):
        self.chat_id = str(chat_id)  # ensure string
        self.user_id = user_id

    def __repr__(self):
        return "<Approve %s>" % self.user_id


<<<<<<< HEAD
Approvals.__table__.create(checkfirst=True)

APPROVE_INSERTION_LOCK = threading.RLock()


def approve(chat_id, user_id):
    with APPROVE_INSERTION_LOCK:
=======
async def approve(chat_id: int | str, user_id: int) -> None:
    "approve an user in the given chat"
    async with SESSION.begin():
>>>>>>> 603ab91 (new updates, dropping this repo too.)
        approve_user = Approvals(str(chat_id), user_id)
        SESSION.add(approve_user)
        SESSION.commit()


<<<<<<< HEAD
def is_approved(chat_id, user_id):
=======
async def is_approved(chat_id: int | str, user_id: int) -> Approvals | None:
    "check if the given user is approved in the chat"
>>>>>>> 603ab91 (new updates, dropping this repo too.)
    try:
        return SESSION.query(Approvals).get((str(chat_id), user_id))
    finally:
<<<<<<< HEAD
        SESSION.close()


def disapprove(chat_id, user_id):
    with APPROVE_INSERTION_LOCK:
        disapprove_user = SESSION.query(Approvals).get((str(chat_id), user_id))
=======
        await SESSION.close()


async def disapprove(chat_id: int | str, user_id: int) -> bool:
    "disapprove an user in the given chat"
    async with SESSION.begin():
        disapprove_user = SESSION.get(Approvals, (str(chat_id), user_id))
>>>>>>> 603ab91 (new updates, dropping this repo too.)
        if disapprove_user:
            SESSION.delete(disapprove_user)
            SESSION.commit()
            return True
        else:
<<<<<<< HEAD
            SESSION.close()
            return False


def list_approved(chat_id):
    try:
        return (
            SESSION.query(Approvals)
            .filter(Approvals.chat_id == str(chat_id))
            .order_by(Approvals.user_id.asc())
            .all()
        )
    finally:
        SESSION.close()
=======
            await SESSION.close()
            return False


async def list_approved(chat_id: int | None) -> list[Approvals]:
    "list number of approved users in the given chat"
    try:
        return SESSION.scalars(
            select(Approvals)
            .filter(Approvals.chat_id == str(chat_id))
            .order_by(Approvals.user_id.asc())
        ).all()
    finally:
        await SESSION.close()
>>>>>>> 603ab91 (new updates, dropping this repo too.)
