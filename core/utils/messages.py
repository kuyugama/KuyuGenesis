from pyrogram import types

from core.database import views


# noinspection PyTypeChecker
def get_difference(view: views.MessageView, message: types.Message) -> dict[str, object]:
    difference = {}

    if view.media_type and message.media:
        if view.media_type == message.media.value:
            if view.media != getattr(message, message.media.value).file_id:
                difference["media"] = getattr(message, message.media.value).file_id
        else:
            difference["media_type"] = message.media.value
            difference["media"] = getattr(message, message.media.value).file_id

    if view.text != message.text:
        difference["text"] = message.text

    return difference
