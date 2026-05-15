import ollama

from utils.config import Config


def _message_content(response) -> str:
    """Extract text from ollama responses across client versions."""
    if hasattr(response, "message") and hasattr(response.message, "content"):
        content = response.message.content or ""
        if content.strip():
            return content
        thinking = getattr(response.message, "thinking", "") or ""
        return thinking
    if isinstance(response, dict):
        message = response.get("message", {})
        if isinstance(message, dict):
            content = message.get("content", "") or ""
            if content.strip():
                return content
            return message.get("thinking", "") or ""
    return str(response)


def send_image_ollama(images_b64: list[str], prompt: str, num_predict: int = 4096):
    response = ollama.chat(
        model=Config.OLLAMA_VISION_MODEL,
        stream=False,
        think=False,
        messages=[
            {
                "role": "user",
                "content": prompt,
                "images": images_b64,
            }
        ],
        options={
            "temperature": 0.1,
            "num_predict": num_predict,
        },
        keep_alive=0,
    )

    return _message_content(response)


def send_text_ollama(prompt: str):
    response = ollama.chat(
        model=Config.OLLAMA_TEXT_MODEL,
        stream=False,
        think=False,
        messages=[{"role": "user", "content": prompt}],
        options={
            "temperature": 1.2,
        },
    )

    return _message_content(response)
