from __future__ import annotations

from app.bootstrap.model.command_registry_deps import CommandRegistryDeps
from app.bootstrap.model.command_registry_result import CommandRegistryResult
from app.common.infrastructure.db.db import db_ro_session
from app.minigame.domain.minigame_repository import MinigameRepository
from app.platform.application.timeout_use_case import TimeoutUseCase
from app.platform.command.application.command_router import CommandRouterImpl
from app.platform.command.ask.application.ask_command_handler import AskCommandHandler
from app.platform.command.ask.application.handle_ask_use_case import HandleAskUseCase
from app.platform.command.balance.application.balance_command_handler import BalanceCommandHandler
from app.platform.command.battle.application.battle_command_handler import BattleCommandHandler
from app.platform.command.battle.application.handle_battle_use_case import HandleBattleUseCase
from app.platform.command.domain.command_router import CommandRouter
from app.platform.domain.repository import PlatformRepository


class CommandRegistry:
    def __init__(
        self,
        deps: CommandRegistryDeps,
        *,
        platform_repository: PlatformRepository,
        minigame_repository: MinigameRepository,
        moderation_service: TimeoutUseCase,
    ):
        self._deps = deps
        self._platform_repository = platform_repository
        self._minigame_repository = minigame_repository
        self._moderation_service = moderation_service

    def build(self) -> CommandRegistryResult:
        bot = self._deps.bot

        followage_command_handler = self._deps.platform.followage_command_handler(
            command_prefix=bot.prefix,
            command_name=bot.command_followage,
            generate_response_use_case_factory=self._deps.ai.generate_response_use_case_factory,
            chat_repository_factory=self._deps.chat.chat_repository_factory,
            conversation_service_factory=self._deps.ai.conversation_service_factory,
            system_prompt_repository_factory=self._deps.ai.system_prompt_repository_factory,
            platform_repository=self._platform_repository,
        )

        ask_command_handler = AskCommandHandler(
            command_prefix=bot.prefix,
            command_name=bot.command_gladdi,
            handle_ask_use_case=HandleAskUseCase(
                get_intent_from_text_use_case_factory=self._deps.ai.get_intent_from_text_use_case_factory,
                prompt_service=self._deps.ai.prompt_service,
                ask_uow_factory=self._deps.ask.ask_uow_factory(
                    chat_repository_factory=self._deps.chat.chat_repository_factory,
                    conversation_service_factory=self._deps.ai.conversation_service_factory,
                    system_prompt_repository_factory=self._deps.ai.system_prompt_repository_factory,
                ),
                generate_response_use_case_factory=self._deps.ai.generate_response_use_case_factory,
                session_factory_ro=db_ro_session,
            ),
        )

        battle_command_handler = BattleCommandHandler(
            command_prefix=bot.prefix,
            command_name=bot.command_fight,
            handle_battle_use_case=HandleBattleUseCase(
                battle_uow=self._deps.battle.battle_uow_factory(
                    economy_policy_factory=self._deps.economy.economy_policy_factory,
                    chat_use_case=self._deps.chat.chat_use_case(),
                    conversation_service_factory=self._deps.ai.conversation_service_factory,
                    get_user_equipment_use_case=self._deps.equipment.get_user_equipment_use_case(),
                ),
                generate_response_use_case_factory=self._deps.ai.generate_response_use_case_factory,
                calculate_timeout_use_case=self._deps.equipment.calculate_timeout_use_case(),
                db_ro_session=db_ro_session,
            ),
            timeout_use_case=self._moderation_service,
        )

        roll_command_handler = self._deps.platform.roll_command_handler(
            command_prefix=bot.prefix,
            command_name=bot.command_roll,
            economy_policy_factory=self._deps.economy.economy_policy_factory,
            betting_service_factory=self._deps.betting.betting_service_factory,
            get_user_equipment_use_case=self._deps.equipment.get_user_equipment_use_case(),
            chat_use_case=self._deps.chat.chat_use_case(),
            roll_cooldown_use_case=self._deps.equipment.roll_cooldown_use_case(),
            calculate_timeout_use_case=self._deps.equipment.calculate_timeout_use_case(),
            timeout_use_case=self._moderation_service,
        )

        balance_command_handler = BalanceCommandHandler(
            handle_balance_use_case=self._deps.economy.handle_balance_use_case(self._deps.chat.chat_use_case())
        )

        bonus_command_handler = self._deps.platform.bonus_command_handler(
            stream_repository_factory=self._deps.stream.stream_repository_factory,
            get_user_equipment_use_case=self._deps.equipment.get_user_equipment_use_case(),
            economy_policy_factory=self._deps.economy.economy_policy_factory,
            chat_use_case=self._deps.chat.chat_use_case(),
        )

        transfer_command_handler = self._deps.platform.transfer_command_handler(
            command_prefix=bot.prefix,
            command_name=bot.command_transfer,
            economy_policy_factory=self._deps.economy.economy_policy_factory,
            chat_use_case=self._deps.chat.chat_use_case(),
        )

        shop_command_handler = self._deps.platform.shop_command_handler(
            command_prefix=bot.prefix,
            command_shop_name=bot.command_shop,
            command_buy_name=bot.command_buy,
            economy_policy_factory=self._deps.economy.economy_policy_factory,
            add_equipment_use_case=self._deps.equipment.add_equipment_use_case(),
            equipment_exists_use_case=self._deps.equipment.equipment_exists_use_case(),
            chat_use_case=self._deps.chat.chat_use_case(),
            shop_item_repository_factory=self._deps.shop.shop_item_repository_factory,
        )

        buy_command_handler = self._deps.platform.buy_command_handler(
            command_prefix=bot.prefix,
            command_buy_name=bot.command_buy,
            economy_policy_factory=self._deps.economy.economy_policy_factory,
            add_equipment_use_case=self._deps.equipment.add_equipment_use_case(),
            equipment_exists_use_case=self._deps.equipment.equipment_exists_use_case(),
            chat_use_case=self._deps.chat.chat_use_case(),
            shop_item_repository_factory=self._deps.shop.shop_item_repository_factory,
        )

        equipment_command_handler = self._deps.platform.equipment_command_handler(
            command_prefix=bot.prefix,
            command_shop=bot.command_shop,
            get_user_equipment_use_case=self._deps.equipment.get_user_equipment_use_case(),
            chat_use_case=self._deps.chat.chat_use_case(),
        )

        top_command_handler = self._deps.platform.top_command_handler(
            economy_policy_factory=self._deps.economy.economy_policy_factory,
            chat_use_case=self._deps.chat.chat_use_case(),
        )

        bottom_command_handler = self._deps.platform.bottom_command_handler(
            economy_policy_factory=self._deps.economy.economy_policy_factory,
            chat_use_case=self._deps.chat.chat_use_case(),
        )

        help_command_handler = self._deps.platform.help_command_handler(
            command_prefix=bot.prefix,
            chat_use_case=self._deps.chat.chat_use_case(),
            commands={
                bot.command_balance,
                bot.command_bonus,
                bot.command_roll,
                bot.command_transfer,
                bot.command_shop,
                bot.command_buy,
                bot.command_equipment,
                bot.command_top,
                bot.command_bottom,
                bot.command_stats,
                bot.command_fight,
                bot.command_gladdi,
                bot.command_followage,
            },
        )

        stats_command_handler = self._deps.platform.stats_command_handler(
            command_prefix=bot.prefix,
            command_name=bot.command_stats,
            economy_policy_factory=self._deps.economy.economy_policy_factory,
            betting_service_factory=self._deps.betting.betting_service_factory,
            battle_use_case=self._deps.battle.battle_use_case(),
            chat_use_case=self._deps.chat.chat_use_case(),
        )

        guess_number_command_handler = self._deps.platform.guess_number_command_handler(
            command_prefix=bot.prefix,
            command_name=bot.command_guess,
            minigame_repository=self._minigame_repository,
            economy_policy_factory=self._deps.economy.economy_policy_factory,
            chat_use_case=self._deps.chat.chat_use_case(),
            get_user_equipment_use_case=self._deps.equipment.get_user_equipment_use_case(),
        )

        guess_letter_command_handler = self._deps.platform.guess_letter_command_handler(
            command_prefix=bot.prefix,
            command_name=bot.command_guess_letter,
            minigame_repository=self._minigame_repository,
            economy_policy_factory=self._deps.economy.economy_policy_factory,
            chat_use_case=self._deps.chat.chat_use_case(),
            get_user_equipment_use_case=self._deps.equipment.get_user_equipment_use_case(),
        )

        guess_word_command_handler = self._deps.platform.guess_word_command_handler(
            command_prefix=bot.prefix,
            command_name=bot.command_guess_word,
            minigame_repository=self._minigame_repository,
            economy_policy_factory=self._deps.economy.economy_policy_factory,
            chat_use_case=self._deps.chat.chat_use_case(),
            get_user_equipment_use_case=self._deps.equipment.get_user_equipment_use_case(),
        )

        rps_command_handler = self._deps.platform.rps_command_handler(
            command_prefix=bot.prefix,
            command_name=bot.command_rps,
            minigame_repository=self._minigame_repository,
            economy_policy_factory=self._deps.economy.economy_policy_factory,
            chat_use_case=self._deps.chat.chat_use_case(),
        )

        command_router: CommandRouter = CommandRouterImpl(bot.prefix)
        command_router.register_command_handler(bot.command_followage, followage_command_handler)
        command_router.register_command_handler(bot.command_gladdi, ask_command_handler)
        command_router.register_command_handler(bot.command_fight, battle_command_handler)
        command_router.register_command_handler(bot.command_roll, roll_command_handler)
        command_router.register_command_handler(bot.command_balance, balance_command_handler)
        command_router.register_command_handler(bot.command_bonus, bonus_command_handler)
        command_router.register_command_handler(bot.command_transfer, transfer_command_handler)
        command_router.register_command_handler(bot.command_shop, shop_command_handler)
        command_router.register_command_handler(bot.command_buy, buy_command_handler)
        command_router.register_command_handler(bot.command_equipment, equipment_command_handler)
        command_router.register_command_handler(bot.command_top, top_command_handler)
        command_router.register_command_handler(bot.command_bottom, bottom_command_handler)
        command_router.register_command_handler(bot.command_help, help_command_handler)
        command_router.register_command_handler(bot.command_stats, stats_command_handler)
        command_router.register_command_handler(bot.command_guess, guess_number_command_handler)
        command_router.register_command_handler(bot.command_guess_letter, guess_letter_command_handler)
        command_router.register_command_handler(bot.command_guess_word, guess_word_command_handler)
        command_router.register_command_handler(bot.command_rps, rps_command_handler)

        return CommandRegistryResult(router=command_router, help_command_handler=help_command_handler)
