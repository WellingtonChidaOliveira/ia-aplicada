from service.llmRouter import LLMClient
from agent.prompts.v1.decidePrompt import decide_prompt
import json
import re
from models.GraphMessage import GraphMessage


def decide_segment(state: GraphMessage, client: LLMClient) -> GraphMessage:
    duration = state.get("duration")

    response = client.llm_router(
        decide_prompt(duration, state.get("analysis"), len(state.get("frames"))),
        options={"temperature": 0.1},
    )

    content = response.strip()
    print(f"Decisão do modelo:\n{content}")

    start_time, end_time = _parse_segment(content, duration)
    print(
        f"Trecho escolhido: {start_time:.2f}s → {end_time:.2f}s ({end_time - start_time:.1f}s)"
    )
    return {"start_time": start_time, "end_time": end_time}


def _parse_segment(content: str, duration: float):
    """Extrai start_time e end_time do JSON retornado pelo modelo.
    Se falhar, retorna o trecho central do vídeo como fallback."""

    try:
        # tenta extrair JSON mesmo se vier com texto ao redor
        match = re.search(r"\{.*?\}", content, re.DOTALL)
        if match:
            data = json.loads(match.group())
            start = float(data["start_time"])
            end = float(data["end_time"])
            return _validar_trecho(start, end, duration)
    except Exception as e:
        print(f"  Falha ao parsear JSON: {e}")

    # fallback: trecho central
    print("  Usando fallback: trecho central do vídeo")
    return _trecho_central(duration)


def _validar_trecho(start: float, end: float, duration: float):
    """Garante que o trecho está dentro dos limites e tem duração válida."""
    start = max(0.0, min(start, duration - 20))
    end = min(duration, max(end, start + 20))

    trecho = end - start
    if trecho < 20:
        end = start + 20
    if trecho > 45:
        end = start + 45

    return round(start, 2), round(end, 2)


def _trecho_central(duration: float):
    """Retorna um trecho de 30s centralizado no vídeo."""
    meio = duration / 2
    start = max(0.0, meio - 15)
    end = start + 30
    return round(start, 2), round(end, 2)
