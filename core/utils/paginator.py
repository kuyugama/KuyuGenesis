import math
from typing import Any

from kgemng import EventManager, NewMessageEvent
from magic_filter import F
from pyrogram.types import Message

from core import Account


def make_pages(elements: list, per_page: int):
    pages = []
    pages_count = math.ceil(len(elements) / per_page)
    for page in range(pages_count):
        pages.append(elements[page * per_page : page * per_page + per_page])

    return pages


class Paginator:
    _parent_event_manager: EventManager | None = None
    _account: Account | None = None

    def __init__(self, event_manager: EventManager):
        self._event_manager = EventManager(enabled=True)
        self._paginators: dict[int, dict[str, Any]] = {}
        self._paginators_messages: dict[int, int] = {}
        self._last_paginator_id = -1

        self._event_manager.register_message_handler(
            self.pager_handler, F.message.text.in_(["<", ">"]) & F.message.reply_to_message.is_not(None)
        )
        event_manager.include_manager(self._event_manager)

        self._parent_event_manager = event_manager

        # Values defined in init() function
        self._ready = False
        self._chat_id = None
        self._message_id = None
        self._edit = None
        self._account = None
        self._allow_to_use_by_others = None

        # Customization values
        self.footer = "{previous_page} [{page}] {next_page}"
        self.previous_page = "<{page}"
        self.next_page = "{page}>"
        self.page_element_separator = "\n\n"
        self.page_element_prefix = ""
        self.page_element_suffix = ""

    @property
    def paginator_id(self):
        self._last_paginator_id += 1
        return self._last_paginator_id

    def _page_text(self, pages: list[str], page):
        return (
            self.page_element_separator.join(
                "{0}{1}{2}".format(
                    self.page_element_prefix, element, self.page_element_suffix
                )
                for element in pages[page - 1]
            )
            + "\n\n"
            + self.footer.format(
                previous_page=self.previous_page.format(page=page - 1)
                if page != 1
                else "",
                page=page,
                next_page=self.next_page.format(page=page + 1)
                if page != len(pages)
                else "",
            ).strip()
        )

    def init(self, message: Message, account: Account, edit: bool = False, allow_to_use_by_others: bool = False):
        self._ready = True
        self._chat_id = message.chat.id
        self._message_id = message.id
        self._account = account
        self._edit = edit
        self._allow_to_use_by_others = allow_to_use_by_others

        return self

    async def make(self, elements: list[str], per_page: int = ...):
        if not self._ready:
            raise ReferenceError("Paginator not ready to making pages. Use Paginator.init first")
        paginator_id = self.paginator_id
        pages = make_pages(elements, per_page)

        if self._edit:
            sent = await self._account.client.edit_message_text(
                chat_id=self._chat_id,
                message_id=self._message_id,
                text=self._page_text(pages, 1),
            )
        else:
            sent = await self._account.client.send_message(
                chat_id=self._chat_id,
                reply_to_message_id=self._message_id,
                text=self._page_text(pages, 1),
            )

        self._paginators[paginator_id] = {
            "pages": pages,
            "current_page": 1,
            "message_id": sent.id,
            "chat_id": self._chat_id,
            "allow_to_use_by_others": self._allow_to_use_by_others,
            "account_id": self._account.info.id,
        }
        self._paginators_messages[sent.id] = paginator_id

    async def pager_handler(self, event: NewMessageEvent):
        increase_page_number = event.message.text == ">"

        if event.message.reply_to_message.id not in self._paginators_messages:
            return event.skip()

        paginator = self._paginators[
            self._paginators_messages[event.message.reply_to_message.id]
        ]

        if not paginator["allow_to_use_by_others"] and not event.message.outgoing:
            return event.skip()

        if (
            increase_page_number
            and len(paginator["pages"]) == paginator["current_page"]
        ) or (not increase_page_number and paginator["current_page"] == 1):
            return await event.message.edit("No one page left")

        if increase_page_number:
            paginator["current_page"] += 1
        else:
            paginator["current_page"] -= 1

        await event.account.client.edit_message_text(
            chat_id=paginator["chat_id"],
            message_id=paginator["message_id"],
            text=self._page_text(paginator["pages"], paginator["current_page"])
        )

        await event.message.delete()
