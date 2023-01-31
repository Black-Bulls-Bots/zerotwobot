import threading
from typing import Union

from zerotwobot.modules.sql import BASE, SESSION
from sqlalchemy import Boolean, Column, Integer, String, BigInteger


class RequestUserSettings(BASE):
    __tablename__ = "user_request_settings"
    user_id = Column(BigInteger, primary_key=True)
    should_request = Column(Boolean, default=True)

    def __init__(self, user_id):
        self.user_id = user_id

    def __repr__(self):
        return "<User request settings ({})>".format(self.user_id)


class RequestChatSettings(BASE):
    __tablename__ = "chat_request_settings"
    chat_id = Column(String(14), primary_key=True)
    should_request = Column(Boolean, default=True)

    def __init__(self, chat_id):
        self.chat_id = str(chat_id)

    def __repr__(self):
        return "<Chat request settings ({})>".format(self.chat_id)


RequestUserSettings.__table__.create(checkfirst=True)
RequestChatSettings.__table__.create(checkfirst=True)




def chat_should_request(chat_id: Union[str, int]) -> bool:
    try:
        chat_setting = SESSION.query(RequestChatSettings).get(str(chat_id))
        if chat_setting:
            return chat_setting.should_request
        return False
    finally:
        await SESSION.close()()


def user_should_request(user_id: int) -> bool:
    try:
        user_setting = SESSION.query(RequestUserSettings).get(user_id)
        if user_setting:
            return user_setting.should_request
        return True
    finally:
        await SESSION.close()()


def set_chat_setting(chat_id: Union[int, str], setting: bool):
    async with SESSION.begin():
        chat_setting = SESSION.query(RequestChatSettings).get(str(chat_id))
        if not chat_setting:
            chat_setting = RequestChatSettings(chat_id)

        chat_setting.should_request = setting
        await SESSION.add(chat_setting)
        await SESSION.commit()


def set_user_setting(user_id: int, setting: bool):
    async with SESSION.begin():
        user_setting = SESSION.query(RequestUserSettings).get(user_id)
        if not user_setting:
            user_setting = RequestUserSettings(user_id)

        user_setting.should_request = setting
        await SESSION.add(user_setting)
        await SESSION.commit()


def migrate_chat(old_chat_id, new_chat_id):
    async with SESSION.begin():
        chat_notes = (
            SESSION.query(RequestChatSettings)
            .filter(RequestChatSettings.chat_id == str(old_chat_id))
            .all()
        )
        for note in chat_notes:
            note.chat_id = str(new_chat_id)
        await SESSION.commit()
