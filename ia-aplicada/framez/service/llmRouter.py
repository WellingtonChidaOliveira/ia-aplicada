from openai import OpenAI
from config.config import Config


class LLMClient:
    def __init__(self):
        self.client = OpenAI(
            base_url=Config.OPENROUTER_BASE_URL,
            api_key=Config.OPENROUTER_API_KEY,
        )

    def llm_router(self, prompt: str, model: str, options: dict = None):
        if options is None:
            options = {}

        completions = self.client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            **options,
        )

        return completions.choices[0].message.content
