from zerotwobot import DEV_USERS, DRAGONS, DEMONS
from telegram import Message
from telegram.ext import MessageFilter


class CustomFilters(object):
    class _Supporters_Filters(MessageFilter):
        def filter(self, message: Message):
            return bool(message.from_user and message.from_user.id in DEMONS)

    support_filter = _Supporters_Filters()

    class Sudoers(MessageFilter):
        def filter(self, message: Message):
            return bool(message.from_user and message.from_user.id in DRAGONS)

    sudo_filter = Sudoers()

    class Developers(MessageFilter):
        def filter(self, message: Message):
            return bool(message.from_user and message.from_user.id in DEV_USERS)

    dev_filter = Developers()

    class _MimeType(MessageFilter):
        def __init__(self, mimetype):
            self.mime_type = mimetype
            self.name = "CustomFilters.mime_type({})".format(self.mime_type)

        def filter(self, message: Message):
            return bool(
                message.document and message.document.mime_type == self.mime_type,
            )

    mime_type = _MimeType

    class _HasText(MessageFilter):
        def filter(self, message: Message):
            return bool(
                message.text
                or message.sticker
                or message.photo
                or message.document
                or message.video,
            )

    has_text = _HasText()

    class _AnonChannel(MessageFilter):

        def filter(self, message: Message):
            return bool(
                message.from_user and message.from_user.id == 136817688
            )

    anonchannel = _AnonChannel
    """Messages that are from `Anonymous Chanels`"""

    class _ForwardChannel(MessageFilter):

        def filter(self, message: Message):
            return bool(
                message.forward_from_chat and message.forward_from_chat.type == "channel"
            )

    forwardchannel = _ForwardChannel
    """Messages that are forwarded from `Channel`"""

    class _ForwardBot(MessageFilter):

        def filter(self, message: Message):
            return bool(
                message.forward_from and message.forward_from.is_bot
            )
    
    forwardbot = _ForwardBot
    """Messages that are forwarded from `Bot`"""