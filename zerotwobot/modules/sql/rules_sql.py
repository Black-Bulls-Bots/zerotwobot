import threading

from zerotwobot.modules.sql import BASE, SESSION
from sqlalchemy import Column, String, UnicodeText, distinct, func


class Rules(BASE):
    __tablename__ = "rules"
    chat_id = Column(String(14), primary_key=True)
    rules = Column(UnicodeText, default="")

    def __init__(self, chat_id):
        self.chat_id = chat_id

    def __repr__(self):
        return "<Chat {} rules: {}>".format(self.chat_id, self.rules)


Rules.__table__.create(checkfirst=True)




def set_rules(chat_id, rules_text):
    async with SESSION.begin():
        rules = SESSION.query(Rules).get(str(chat_id))
        if not rules:
            rules = Rules(str(chat_id))
        rules.rules = rules_text

        await SESSION.add(rules)
        await SESSION.commit()


def get_rules(chat_id):
    rules = SESSION.query(Rules).get(str(chat_id))
    ret = ""
    if rules:
        ret = rules.rules

    await SESSION.close()()
    return ret


def num_chats():
    try:
        return SESSION.query(func.count(distinct(Rules.chat_id))).scalar()
    finally:
        await SESSION.close()()


def migrate_chat(old_chat_id, new_chat_id):
    async with SESSION.begin():
        chat = SESSION.query(Rules).get(str(old_chat_id))
        if chat:
            chat.chat_id = str(new_chat_id)
        await SESSION.commit()
