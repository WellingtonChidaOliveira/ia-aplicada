import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
    OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"
    # MODEL_LLM_DECIDE = "nvidia/nemotron-3-super-120b-a12b:free"
    MODEL_LLM_DECIDE = "openai/gpt-4o-mini"
    MODEL_LLM_PHRASE = "openai/gpt-4o-mini"
    OLLAMA_VISION_MODEL = os.getenv("OLLAMA_VISION_MODEL", "qwen3-vl:8b")
    OLLAMA_TEXT_MODEL = os.getenv("OLLAMA_TEXT_MODEL", "llama3.1:latest")

    VIDEO_CRF = os.getenv("VIDEO_CRF", "18")
    VIDEO_PRESET = os.getenv("VIDEO_PRESET", "slow")
    VIDEO_AUDIO_BITRATE = os.getenv("VIDEO_AUDIO_BITRATE", "192k")

    MIN_CONTENT_LENGTH = 30
    RETRY_SLEEP_SECONDS = 2
    FRAME_SLEEP_SECONDS = 3
    UNAVAILABLE_LABEL = "[analysis unavailable]"

    RETRIES_ANALYSE = 3
    TOP_N = 3
