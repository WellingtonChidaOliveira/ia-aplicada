import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
    OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"
    MODEL_LLM_DECIDE = "nvidia/nemotron-3-super-120b-a12b:free"
    MODEL_LLM_PHRASE = "minimax/minimax-m2.5:free"
