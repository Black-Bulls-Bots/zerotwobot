import threading

from sqlalchemy import Column, String, BigInteger, select

from zerotwobot.modules.sql import BASE, SESSION


class Approvals(BASE):
    __tablename__ = "approval"
    chat_id: str = Column(String(14), primary_key=True)
    user_id: int = Column(BigInteger, primary_key=True)

    def __init__(self, chat_id: int | str, user_id: int):
        self.chat_id = str(chat_id)  # ensure string
        self.user_id = user_id

    def __repr__(self):
        return "<Approve %s>" % self.user_id


Approvals.__table__.create(checkfirst=True)




async def approve(chat_id: int | str, user_id: int) -> None:
    async with SESSION.begin():
        approve_user = Approvals(str(chat_id), user_id)
        await SESSION.add(approve_user)
        await SESSION.commit()


async def is_approved(chat_id: int | str, user_id: int) -> Approvals | None:
    try:
        return SESSION.get(Approvals, (str(chat_id), user_id))
    finally:
        await SESSION.close()()


async def disapprove(chat_id: int | str, user_id: int) -> bool:
    async with SESSION.begin():
        disapprove_user = SESSION.get(Approvals, (str(chat_id), user_id))
        if disapprove_user:
            SESSION.delete(disapprove_user)
            await SESSION.commit()
            return True
        else:
            await SESSION.close()()
            return False



async def list_approved(chat_id: int | None) -> list[Approvals]:
    try:
        return (
            SESSION.scalars(
            select(Approvals)
            .filter(Approvals.chat_id == str(chat_id))
            .order_by(Approvals.user_id.asc())
        ).all()
        )
    finally:
        await SESSION.close()()
