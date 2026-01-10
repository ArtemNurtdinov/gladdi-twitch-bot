import asyncio
import unittest

from app.twitch.infrastructure.twitch_chat_client import TwitchCommandRouter
from core.chat.interfaces import ChatContext, ChatMessage


class FakeChatContext:
    def __init__(self, channel: str, author: str):
        self.channel = channel
        self.author = author
        self.author_id = None

    async def reply(self, text: str) -> None:
        return None

    async def send_channel(self, text: str) -> None:
        return None


class FakeMessage(ChatMessage):
    def __init__(self, channel: str, author: str, text: str):
        self.channel = channel
        self.author = author
        self.text = text


class TestTwitchCommandRouter(unittest.IsolatedAsyncioTestCase):
    async def test_dispatch_passes_context_without_shared_state(self):
        router = TwitchCommandRouter(prefix="!")
        seen: list[tuple[str, str]] = []

        async def handler(ctx: ChatContext, msg: ChatMessage):
            await asyncio.sleep(0.01)
            seen.append((ctx.author, msg.text))

        router.register("ping", handler)

        msg1 = FakeMessage(channel="chan", author="alice", text="!ping hello")
        msg2 = FakeMessage(channel="chan", author="bob", text="!ping there")
        ctx1 = FakeChatContext(channel="chan", author="alice")
        ctx2 = FakeChatContext(channel="chan", author="bob")

        results = await asyncio.gather(
            router.dispatch(msg1, ctx1),
            router.dispatch(msg2, ctx2),
        )

        self.assertEqual(results, [True, True])
        self.assertCountEqual(seen, [("alice", "!ping hello"), ("bob", "!ping there")])
