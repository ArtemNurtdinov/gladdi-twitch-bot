from app.commands.registry import CommandRegistry
from app.platform.bot.bot import Bot
from app.platform.bot.bot_settings import BotSettings
from core.chat.interfaces import ChatMessage, CommandRouter
from core.chat.prefix_command_router import PrefixCommandRouter


def build_twitch_command_router(settings: BotSettings, registry: CommandRegistry, bot: Bot) -> CommandRouter:
    router = PrefixCommandRouter(settings.prefix)

    async def followage_handler(chat_ctx, msg: ChatMessage):
        await registry.followage.handle(channel_name=chat_ctx.channel, display_name=chat_ctx.author, chat_ctx=chat_ctx)

    async def ask_handler(chat_ctx, msg: ChatMessage):
        await registry.ask.handle(channel_name=chat_ctx.channel, full_message=msg.text, display_name=chat_ctx.author, chat_ctx=chat_ctx)

    async def battle_handler(chat_ctx, msg: ChatMessage):
        await registry.battle.handle(
            channel_name=chat_ctx.channel,
            display_name=chat_ctx.author,
            battle_waiting_user_ref=bot.battle_waiting_user_ref,
            chat_ctx=chat_ctx,
        )

    async def roll_handler(chat_ctx, msg: ChatMessage):
        tail = msg.text[len(settings.prefix + settings.command_roll) :].strip()
        amount = tail or None
        await registry.roll.handle(chat_ctx=chat_ctx, channel_name=chat_ctx.channel, display_name=chat_ctx.author, amount=amount)

    async def balance_handler(chat_ctx, msg: ChatMessage):
        await registry.balance.handle(channel_name=chat_ctx.channel, display_name=chat_ctx.author, chat_ctx=chat_ctx)

    async def bonus_handler(chat_ctx, msg: ChatMessage):
        await registry.bonus.handle(channel_name=chat_ctx.channel, display_name=chat_ctx.author, chat_ctx=chat_ctx)

    async def transfer_handler(chat_ctx, msg: ChatMessage):
        tail = msg.text[len(settings.prefix + settings.command_transfer) :].strip()
        recipient = None
        amount = None
        if tail:
            parts = tail.split()
            if parts:
                recipient = parts[0]
                if len(parts) > 1:
                    amount = parts[1]
        await registry.transfer.handle(
            channel_name=chat_ctx.channel,
            sender_display_name=chat_ctx.author,
            chat_ctx=chat_ctx,
            recipient=recipient,
            amount=amount,
        )

    async def shop_handler(chat_ctx, msg: ChatMessage):
        await registry.shop.handle_shop(channel_name=chat_ctx.channel, display_name=chat_ctx.author, chat_ctx=chat_ctx)

    async def buy_handler(chat_ctx, msg: ChatMessage):
        tail = msg.text[len(settings.prefix + settings.command_buy) :].strip()
        item_name = tail or None
        await registry.shop.handle_buy(channel_name=chat_ctx.channel, display_name=chat_ctx.author, chat_ctx=chat_ctx, item_name=item_name)

    async def equipment_handler(chat_ctx, msg: ChatMessage):
        await registry.equipment.handle(channel_name=chat_ctx.channel, display_name=chat_ctx.author, chat_ctx=chat_ctx)

    async def top_handler(chat_ctx, msg: ChatMessage):
        await registry.top_bottom.handle_top(channel_name=chat_ctx.channel, chat_ctx=chat_ctx)

    async def bottom_handler(chat_ctx, msg: ChatMessage):
        await registry.top_bottom.handle_bottom(channel_name=chat_ctx.channel, chat_ctx=chat_ctx)

    async def help_handler(chat_ctx, msg: ChatMessage):
        await registry.help.handle(channel_name=chat_ctx.channel, chat_ctx=chat_ctx)

    async def stats_handler(chat_ctx, msg: ChatMessage):
        await registry.stats.handle(channel_name=chat_ctx.channel, display_name=chat_ctx.author, chat_ctx=chat_ctx)

    async def guess_number_handler(chat_ctx, msg: ChatMessage):
        tail = msg.text[len(settings.prefix + settings.command_guess) :].strip()
        number = tail or None
        await registry.guess.handle_guess_number(channel_name=chat_ctx.channel, display_name=chat_ctx.author, chat_ctx=chat_ctx, number=number)

    async def guess_letter_handler(chat_ctx, msg: ChatMessage):
        tail = msg.text[len(settings.prefix + settings.command_guess_letter) :].strip()
        letter = tail or None
        await registry.guess.handle_guess_letter(channel_name=chat_ctx.channel, display_name=chat_ctx.author, chat_ctx=chat_ctx, letter=letter)

    async def guess_word_handler(chat_ctx, msg: ChatMessage):
        tail = msg.text[len(settings.prefix + settings.command_guess_word) :].strip()
        word = tail or None
        await registry.guess.handle_guess_word(channel_name=chat_ctx.channel, display_name=chat_ctx.author, chat_ctx=chat_ctx, word=word)

    async def rps_handler(chat_ctx, msg: ChatMessage):
        tail = msg.text[len(settings.prefix + settings.command_rps) :].strip()
        choice = tail or None
        await registry.rps.handle(channel_name=chat_ctx.channel, display_name=chat_ctx.author, chat_ctx=chat_ctx, choice=choice)

    router.register(settings.command_followage, followage_handler)
    router.register(settings.command_gladdi, ask_handler)
    router.register(settings.command_fight, battle_handler)
    router.register(settings.command_roll, roll_handler)
    router.register(settings.command_balance, balance_handler)
    router.register(settings.command_bonus, bonus_handler)
    router.register(settings.command_transfer, transfer_handler)
    router.register(settings.command_shop, shop_handler)
    router.register(settings.command_buy, buy_handler)
    router.register(settings.command_equipment, equipment_handler)
    router.register(settings.command_top, top_handler)
    router.register(settings.command_bottom, bottom_handler)
    router.register(settings.command_help, help_handler)
    router.register(settings.command_stats, stats_handler)
    router.register(settings.command_guess, guess_number_handler)
    router.register(settings.command_guess_letter, guess_letter_handler)
    router.register(settings.command_guess_word, guess_word_handler)
    router.register(settings.command_rps, rps_handler)

    return router
