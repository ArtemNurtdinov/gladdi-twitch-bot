from abc import ABC, abstractmethod


class GuessCommandHandler(ABC):
    @abstractmethod
    async def handle_guess_number(self, channel_name: str, display_name: str, number: str | None): ...
    @abstractmethod
    async def handle_guess_letter(self, channel_name: str, display_name: str, letter: str | None): ...
    @abstractmethod
    async def handle_guess_word(self, channel_name: str, display_name: str, word: str | None): ...
