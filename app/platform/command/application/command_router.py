from app.commands.commands_registry import CommandRegistry
from app.platform.bot.model.bot_settings import BotSettings
from app.platform.command.application.prefix_command_router import PrefixCommandRouter
from app.platform.command.domain.command_handler import CommandHandler
from app.platform.command.domain.command_router import CommandRouter


def build_twitch_command_router(
    settings: BotSettings, registry: CommandRegistry, battle_waiting_user: dict[str, str | None]
) -> CommandRouter:
    router = PrefixCommandRouter(settings.prefix)

    class FollowageHandler(CommandHandler):
        async def handle_command(self, channel_name: str, user_name: str, user_message: str):
            await registry.followage_command_handler.handle(channel_name=channel_name, display_name=user_name)

    class AskHandler(CommandHandler):
        async def handle_command(self, channel_name: str, user_name: str, user_message: str):
            await registry.ask_command_handler.handle(channel_name, user_message, user_name)

    class BattleHandler(CommandHandler):
        async def handle_command(self, channel_name: str, user_name: str, user_message: str):
            await registry.battle_command_handler.handle(
                channel_name=channel_name, display_name=user_name, battle_waiting_user=battle_waiting_user
            )

    class RollHandler(CommandHandler):
        async def handle_command(self, channel_name: str, user_name: str, user_message: str):
            tail = user_message[len(settings.prefix + settings.command_roll) :].strip()
            amount = tail or None
            await registry.roll_command_handler.handle(channel_name=channel_name, display_name=user_name, amount=amount)

    class BalanceHandler(CommandHandler):
        async def handle_command(self, channel_name: str, user_name: str, user_message: str):
            await registry.balance_command_handler.handle(channel_name=channel_name, display_name=user_name)

    class BonusHandler(CommandHandler):
        async def handle_command(self, channel_name: str, user_name: str, user_message: str):
            await registry.bonus_command_handler.handle(channel_name=channel_name, display_name=user_name)

    class TransferHandler(CommandHandler):
        async def handle_command(self, channel_name: str, user_name: str, user_message: str):
            tail = user_message[len(settings.prefix + settings.command_transfer) :].strip()
            recipient = None
            amount = None
            if tail:
                parts = tail.split()
                if parts:
                    recipient = parts[0]
                    if len(parts) > 1:
                        amount = parts[1]
            await registry.transfer_command_handler.handle(
                channel_name=channel_name,
                sender_display_name=user_name,
                recipient=recipient,
                amount=amount,
            )

    class ShopHandler(CommandHandler):
        async def handle_command(self, channel_name: str, user_name: str, user_message: str):
            await registry.shop_command_handler.handle_shop(channel_name=channel_name, display_name=user_name)

    class BuyHandler(CommandHandler):
        async def handle_command(self, channel_name: str, user_name: str, user_message: str):
            tail = user_message[len(settings.prefix + settings.command_buy) :].strip()
            item_name = tail or None
            await registry.shop_command_handler.handle_buy(channel_name=channel_name, display_name=user_name, item_name=item_name)

    class EquipmentHandler(CommandHandler):
        async def handle_command(self, channel_name: str, user_name: str, user_message: str):
            await registry.equipment_command_handler.handle(channel_name=channel_name, display_name=user_name)

    class TopHandler(CommandHandler):
        async def handle_command(self, channel_name: str, user_name: str, user_message: str):
            await registry.top_bottom_command_handler.handle_top(channel_name=channel_name, display_name=user_name)

    class BottomHandler(CommandHandler):
        async def handle_command(self, channel_name: str, user_name: str, user_message: str):
            await registry.top_bottom_command_handler.handle_bottom(channel_name=channel_name, display_name=user_name)

    class HelpHandler(CommandHandler):
        async def handle_command(self, channel_name: str, user_name: str, user_message: str):
            await registry.help_command_handler.handle(channel_name=channel_name, display_name=user_name)

    class StatsHandler(CommandHandler):
        async def handle_command(self, channel_name: str, user_name: str, user_message: str):
            await registry.stats_command_handler.handle(channel_name=channel_name, display_name=user_name)

    class GuessNumberHandler(CommandHandler):
        async def handle_command(self, channel_name: str, user_name: str, user_message: str):
            tail = user_message[len(settings.prefix + settings.command_guess) :].strip()
            number = tail or None
            await registry.guess_command_handler.handle_guess_number(channel_name=channel_name, display_name=user_name, number=number)

    class GuessLetterHandler(CommandHandler):
        async def handle_command(self, channel_name: str, user_name: str, user_message: str):
            tail = user_message[len(settings.prefix + settings.command_guess_letter) :].strip()
            letter = tail or None
            await registry.guess_command_handler.handle_guess_letter(channel_name=channel_name, display_name=user_name, letter=letter)

    class GuessWordHandler(CommandHandler):
        async def handle_command(self, channel_name: str, user_name: str, user_message: str):
            tail = user_message[len(settings.prefix + settings.command_guess_word) :].strip()
            word = tail or None
            await registry.guess_command_handler.handle_guess_word(channel_name=channel_name, display_name=user_name, word=word)

    class RpsHandler(CommandHandler):
        async def handle_command(self, channel_name: str, user_name: str, user_message: str):
            tail = user_message[len(settings.prefix + settings.command_rps) :].strip()
            choice = tail or None
            await registry.rps_command_handler.handle(channel_name=channel_name, display_name=user_name, choice=choice)

    followage_handler = FollowageHandler()
    ask_handler = AskHandler()
    battle_handler = BattleHandler()
    roll_handler = RollHandler()
    balance_handler = BalanceHandler()
    bonus_handler = BonusHandler()
    transfer_handler = TransferHandler()
    shop_handler = ShopHandler()
    buy_handler = BuyHandler()
    equipment_handler = EquipmentHandler()
    top_handler = TopHandler()
    bottom_handler = BottomHandler()
    help_handler = HelpHandler()
    stats_handler = StatsHandler()
    guess_number_handler = GuessNumberHandler()
    guess_letter_handler = GuessLetterHandler()
    guess_word_handler = GuessWordHandler()
    rps_handler = RpsHandler()

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
