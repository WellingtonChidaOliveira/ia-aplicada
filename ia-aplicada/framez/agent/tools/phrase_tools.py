from langchain.tools import tool
from service.llm_router import LLMClient
from service.ollama import send_text_ollama
from agent.prompts.v4.generate_phrase import generate_phrase_prompt
from utils.config import Config


@tool
def generate_phrase() -> dict:
    """
    Generates a dark motivational phrase based on the video segment reason.
    Input: reason (from decide_segment)
    Returns: a dict with the generated phrase.
    """
    client = LLMClient()
    try:
        response = client.llm_router(
            prompt=generate_phrase_prompt(),
            model=Config.MODEL_LLM_PHRASE,
            options={
                "temperature": 1.2,
                "top_p": 0.95,
                "frequency_penalty": 1.0,
                "presence_penalty": 0.8,
            },
        )
        return {"phrase": response.strip()}
    except Exception as e:
        print(f"   Falha ao gerar frase no OpenRouter: {e}")
        print("   Usando fallback local (Ollama)...")
        try:
            return {"phrase": send_text_ollama(generate_phrase_prompt())}
        except Exception as ollama_e:
            print(f"   Falha também no Ollama: {ollama_e}")
            return {"phrase": "A persistência é o caminho para o êxito."}
