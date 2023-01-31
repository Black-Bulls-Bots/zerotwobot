import threading

from zerotwobot import application
from zerotwobot.modules.sql import BASE, SESSION
from sqlalchemy import (
    Column,
    ForeignKey,
    Integer,
    BigInteger,
    String,
    UnicodeText,
    UniqueConstraint,
    func,
)


class Users(BASE):
    __tablename__ = "users"
    user_id = Column(BigInteger, primary_key=True)
    username = Column(UnicodeText)

    def __init__(self, user_id, username=None):
        self.user_id = user_id
        self.username = username

    def __repr__(self):
        return "<User {} ({})>".format(self.username, self.user_id)


class Chats(BASE):
    __tablename__ = "chats"
    chat_id = Column(String(14), primary_key=True)
    chat_name = Column(UnicodeText, nullable=False)

    def __init__(self, chat_id, chat_name):
        self.chat_id = str(chat_id)
        self.chat_name = chat_name

    def __repr__(self):
        return "<Chat {} ({})>".format(self.chat_name, self.chat_id)


class ChatMembers(BASE):
    __tablename__ = "chat_members"
    priv_chat_id = Column(Integer, primary_key=True)
    # NOTE: Use dual primary key instead of private primary key?
    chat = Column(
        String(14),
        ForeignKey("chats.chat_id", onupdate="CASCADE", ondelete="CASCADE"),
        nullable=False,
    )
    user = Column(
        BigInteger,
        ForeignKey("users.user_id", onupdate="CASCADE", ondelete="CASCADE"),
        nullable=False,
    )
    __table_args__ = (UniqueConstraint("chat", "user", name="_chat_members_uc"),)

    def __init__(self, chat, user):
        self.chat = chat
        self.user = user

    def __repr__(self):
        return "<Chat user {} ({}) in chat {} ({})>".format(
            self.user.username,
            self.user.user_id,
            self.chat.chat_name,
            self.chat.chat_id,
        )


Users.__table__.create(checkfirst=True)
Chats.__table__.create(checkfirst=True)
ChatMembers.__table__.create(checkfirst=True)



def ensure_bot_in_db():
    async with SESSION.begin():
        bot = Users(application.bot.id, application.bot.username)
        SESSION.merge(bot)
        await SESSION.commit()


def update_user(user_id, username, chat_id=None, chat_name=None):
    async with SESSION.begin():
        user = SESSION.query(Users).get(user_id)
        if not user:
            user = Users(user_id, username)
            await SESSION.add(user)
            SESSION.flush()
        else:
            user.username = username

        if not chat_id or not chat_name:
            await SESSION.commit()
            return

        chat = SESSION.query(Chats).get(str(chat_id))
        if not chat:
            chat = Chats(str(chat_id), chat_name)
            await SESSION.add(chat)
            SESSION.flush()

        else:
            chat.chat_name = chat_name

        member = (
            SESSION.query(ChatMembers)
            .filter(ChatMembers.chat == chat.chat_id, ChatMembers.user == user.user_id)
            .first()
        )
        if not member:
            chat_member = ChatMembers(chat.chat_id, user.user_id)
            await SESSION.add(chat_member)

        await SESSION.commit()


def get_userid_by_name(username):
    try:
        return (
            SESSION.query(Users)
            .filter(func.lower(Users.username) == username.lower())
            .all()
        )
    finally:
        await SESSION.close()()


def get_name_by_userid(user_id):
    try:
        return SESSION.query(Users).get(Users.user_id == int(user_id)).first()
    finally:
        await SESSION.close()()


def get_chat_members(chat_id):
    try:
        return SESSION.query(ChatMembers).filter(ChatMembers.chat == str(chat_id)).all()
    finally:
        await SESSION.close()()


def get_all_chats():
    try:
        return SESSION.query(Chats).all()
    finally:
        await SESSION.close()()


def get_all_users():
    try:
        return SESSION.query(Users).all()
    finally:
        await SESSION.close()()


def get_user_num_chats(user_id):
    try:
        return (
            SESSION.query(ChatMembers).filter(ChatMembers.user == int(user_id)).count()
        )
    finally:
        await SESSION.close()()


def get_user_com_chats(user_id):
    try:
        chat_members = (
            SESSION.query(ChatMembers).filter(ChatMembers.user == int(user_id)).all()
        )
        return [i.chat for i in chat_members]
    finally:
        await SESSION.close()()


def num_chats():
    try:
        return SESSION.query(Chats).count()
    finally:
        await SESSION.close()()


def num_users():
    try:
        return SESSION.query(Users).count()
    finally:
        await SESSION.close()()


def migrate_chat(old_chat_id, new_chat_id):
    async with SESSION.begin():
        chat = SESSION.query(Chats).get(str(old_chat_id))
        if chat:
            chat.chat_id = str(new_chat_id)
        await SESSION.commit()

        chat_members = (
            SESSION.query(ChatMembers)
            .filter(ChatMembers.chat == str(old_chat_id))
            .all()
        )
        for member in chat_members:
            member.chat = str(new_chat_id)
        await SESSION.commit()


ensure_bot_in_db()


def del_user(user_id):
    async with SESSION.begin():
        curr = SESSION.query(Users).get(user_id)
        if curr:
            SESSION.delete(curr)
            await SESSION.commit()
            return True

        ChatMembers.query.filter(ChatMembers.user == user_id).delete()
        await SESSION.commit()
        await SESSION.close()()
    return False


def rem_chat(chat_id):
    async with SESSION.begin():
        chat = SESSION.query(Chats).get(str(chat_id))
        if chat:
            SESSION.delete(chat)
            await SESSION.commit()
        else:
            await SESSION.close()()
