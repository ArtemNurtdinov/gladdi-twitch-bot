class PromptService:
    def get_jackbox_prompt(self, nickname: str, message: str) -> str:
        return (
            f"Сообщение от пользователя с никнеймом {nickname}: {message}."
            f"\n\n Если вопрос связан с тем, когда будет игра jackbox, "
            f"то ответь, что никогда не будет и что поднимать эту тему запрещено на этом канале!"
        )

    def get_skuf_femboy_prompt(self, nickname: str, message: str) -> str:
        return (
            f"Сообщение от пользователя с никнеймом {nickname}: {message}.\n\nЕсли вопрос связан с тем, кто и на сколько % скуф или фембой, "
            f"то вот дополнительная информация:"
            f"\n@ArtemNeFRiT — 43% скуф, 12% фембой"
            f"\n@d3ar_88 — 28% скуф, 27% фембой"
            f"\n@dankar1000 — 61% скуф, 9% фембой"
            f"\n@Gidrovlad — 47% скуф, 35% фембой"
            f"\n@crazyg1mer — 73% скуф, 62% фембой"
            f"\n@pr9mo_mejdy_bylochek — 37% скуф"
            f"\n@tikva_cheel12 — 34% скуф, 19% фембой"
            f"\n@voidterror — 92% скуф, 24% фембой"
        )

    def get_dankar_cut_prompt(self, nickname: str, message: str) -> str:
        return (
            f"Сообщение от пользователя с никнеймом {nickname}: {message}."
            f"\n\nЕсли сообщение связано с просмотром нарезки, то ответь, что поднимать эту тему запрещено на этом канале!"
        )

    def get_hello_prompt(self, nickname: str, message: str) -> str:
        return (
            f"Сообщение от пользователя с никнеймом {nickname}: {message}."
            f"\nЕсли сообщение содержит в себе приветствие, поприветствуй его в ответ."
            f"\nЕсли сообщение не содержит приветствие, просто забавно прокомментируй его."
        )

    def get_default_prompt(self, nickname: str, message: str) -> str:
        return f"Ответь пользователю с никнеймом {nickname} на его сообщение: {message}."



