import asyncio
import unittest
from dataclasses import dataclass

from core.chat.interfaces import ChatContext, ChatMessage
from core.chat.prefix_command_router import PrefixCommandRouter


@dataclass(slots=True)
class FakeChatContext(ChatContext):
    _channel: str
    _author: str

    def __init__(self, channel: str, author: str):
        self._channel = channel
        self._author = author

    @property
    def channel(self) -> str:
        return self._channel

    @property
    def author(self) -> str:
        return self._author

    async def send_channel(self, text: str) -> None:
        return None


def make_message(author: str, text: str) -> ChatMessage:
    return ChatMessage(author=author, text=text, author_id=f"{author}_id")


class TestPrefixCommandRouter(unittest.IsolatedAsyncioTestCase):
    async def test_dispatch_passes_context_without_shared_state(self):
        router = PrefixCommandRouter(prefix="!")
        seen: list[tuple[str, str]] = []

        async def handler(ctx: ChatContext, msg: ChatMessage):
            await asyncio.sleep(0.01)
            seen.append((msg.author, msg.text))

        router.register("ping", handler)

        contexts = (
            (make_message("alice", "!ping hello"), FakeChatContext(channel="chan", author="alice")),
            (make_message("bob", "!ping there"), FakeChatContext(channel="chan", author="bob")),
        )

        results = await asyncio.gather(*(router.dispatch(msg, ctx) for msg, ctx in contexts))

        self.assertEqual(results, [True, True])
        self.assertCountEqual(seen, [("alice", "!ping hello"), ("bob", "!ping there")])
