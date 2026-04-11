from openai import OpenAI
from config.config import Config


class LLMClient:
    def __init__(self):
        self.client = OpenAI(
            base_url=Config.OPENROUTER_BASE_URL,
            api_key=Config.OPENROUTER_API_KEY,
        )

    def llm_router(self, prompt: str, options: dict = None, images: list = None):
        if options is None:
            options = {}

        completions = self.client.chat.completions.create(
            model=Config.MODEL_LLM,
            messages=[{"role": "user", "content": prompt}],
            **options,
        )

        return completions.choices[0].message.content
