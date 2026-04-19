from service import ollama
from service.llmRouter import LLMClient
from agent.prompts.v1.decidePrompt import decide_prompt
import json
import re
from models.GraphMessage import GraphMessage
from config.config import Config

TOP_N = 3


def decide_segment(state: GraphMessage, client: LLMClient) -> GraphMessage:
    duration = state.get("duration")

    response = ollama.send_text_ollama(
        decide_prompt(duration, state.get("analysis"), len(state.get("frames"))),
    )

    content = response.strip()
    print(f"Decisão do modelo:\n{content}")

    segments = _parse_segments(content, duration)

    for i, seg in enumerate(segments, start=1):
        print(
            f"  Top {i}: {seg['start_time']:.2f}s → {seg['end_time']:.2f}s "
            f"({seg['end_time'] - seg['start_time']:.1f}s) — {seg.get('reason', '')}"
        )

    return {"segments": segments}


def _parse_segments(content: str, duration: float) -> list[dict]:
    """Extrai até TOP_N segmentos do JSON retornado pelo modelo.
    Valida cada trecho; preenche com fallbacks se necessário."""

    parsed = []
    try:
        match = re.search(r"\{.*\}", content, re.DOTALL)
        if match:
            data = json.loads(match.group())
            trechos = data.get("trechos", [])
            for item in trechos[:TOP_N]:
                start = float(item["start_time"])
                end = float(item["end_time"])
                start, end = _validar_trecho(start, end, duration)
                parsed.append(
                    {
                        "rank": item.get("rank", len(parsed) + 1),
                        "start_time": start,
                        "end_time": end,
                        "reason": item.get("reason", ""),
                    }
                )
    except Exception as e:
        print(f"  Falha ao parsear JSON: {e}")

    # preenche com fallbacks caso o modelo tenha retornado menos de TOP_N
    if len(parsed) < TOP_N:
        print(
            f"  Modelo retornou {len(parsed)} trecho(s); completando com fallbacks..."
        )
        fallbacks = _gerar_fallbacks(duration, TOP_N - len(parsed), parsed)
        parsed.extend(fallbacks)

    return parsed[:TOP_N]


def _validar_trecho(start: float, end: float, duration: float):
    """Garante que o trecho está dentro dos limites e tem duração válida (20–45s)."""
    start = max(0.0, min(start, duration - 20))
    end = min(duration, max(end, start + 20))

    trecho = end - start
    if trecho < 20:
        end = start + 20
    if trecho > 45:
        end = start + 45

    return round(start, 2), round(end, 2)


def _gerar_fallbacks(duration: float, n: int, existing: list[dict]) -> list[dict]:
    """Gera n trechos de 30s espaçados uniformemente no vídeo,
    evitando sobreposição com trechos já existentes."""
    fallbacks = []
    # divide o vídeo em n+1+len(existing) fatias e pega pontos intermediários
    total_points = n + len(existing) + 1
    step = duration / total_points

    existing_starts = {seg["start_time"] for seg in existing}
    rank = len(existing) + 1

    for i in range(1, total_points):
        if len(fallbacks) >= n:
            break
        candidate_start = round(i * step, 2)
        # evita sobreposição grosseira com os já existentes
        if any(abs(candidate_start - es) < 20 for es in existing_starts):
            continue
        candidate_start = max(0.0, min(candidate_start, duration - 30))
        candidate_end = round(candidate_start + 30, 2)
        fallbacks.append(
            {
                "rank": rank,
                "start_time": candidate_start,
                "end_time": candidate_end,
                "reason": "fallback automático",
            }
        )
        existing_starts.add(candidate_start)
        rank += 1

    return fallbacks
