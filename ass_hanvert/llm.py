from .converter import Converter, Direction

_DEFAULT_S2T_PROMPT = (
    "Convert the following text accurately to Taiwan Traditional Chinese, strictly preserving all "
    "original formatting (including punctuation, spaces, newlines, etc.). Output only the converted result.\n"
    "Follow these rules during conversion:\n"
    "- Use Taiwan standard character mappings and conventional vocabulary.\n"
    "- Properly translate technical terms and proper nouns into Taiwan usage.\n"
    "- Adjust colloquial expressions and internet slang to natural, common Taiwan usage based on context."
)

_DEFAULT_T2S_PROMPT = (
    "Convert the following text accurately to Simplified Chinese, strictly preserving all "
    "original formatting (including punctuation, spaces, newlines, etc.). Output only the converted result.\n"
    "Follow these rules during conversion:\n"
    "- Use standard Simplified Chinese character mappings and conventional vocabulary.\n"
    "- Properly translate technical terms and proper nouns into Mainland China usage.\n"
    "- Adjust colloquial expressions and internet slang to natural, common usage based on context."
)


class OpenAIConverter(Converter):
    def __init__(
        self,
        base_url: str,
        model: str,
        api_key: str,
        system_prompt: str | None = None,
        temperature: float = 0.1,
        direction: Direction | None = None,
    ) -> None:
        super().__init__()
        self.base_url = base_url
        self.api_key = api_key
        self.model = model
        self.direction = direction if direction is not None else Direction.S2T
        self.system_prompt = (
            system_prompt
            if system_prompt is not None
            else (_DEFAULT_T2S_PROMPT if self.direction == Direction.T2S else _DEFAULT_S2T_PROMPT)
        )
        self.temperature = temperature

    def _do_convert(self, text: str) -> str:
        import openai

        client = openai.Client(api_key=self.api_key, base_url=self.base_url)
        response = client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": self.system_prompt},
                {"role": "user", "content": text},
            ],
            temperature=self.temperature,
            stream=False,
        )
        return response.choices[0].message.content
