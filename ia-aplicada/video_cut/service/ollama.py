import os
import ollama
import base64
import service.prompt.v1.analisysVideo as prompt_analisys_video
import time


def carregar_base64(path: str) -> str:
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")


def analise_frame(frame_path: str, frame_num: int, total: int, retries: int = 3) -> str:
    img_b64 = carregar_base64(frame_path)

    for tentativa in range(1, retries + 1):
        try:
            response = ollama.chat(
                model="qwen3-vl:8b",
                stream=False,
                messages=[
                    {
                        "role": "user",
                        "content": (
                            f"Frame {frame_num}/{total} de um vídeo de treino de musculação. "
                            "Descreva em 2-3 linhas: nível de esforço (baixo/médio/alto), "
                            "exercício ou posição, expressão do atleta."
                        ),
                        "images": [img_b64],
                    }
                ],
                options={
                    "temperature": 0.1,
                    "num_predict": 256,
                },
            )
            content = response.message.content.strip()
            if content:
                return content
            print(f"    Tentativa {tentativa} vazia, repetindo...")
        except Exception as e:
            print(f"    Tentativa {tentativa} falhou: {e}")

        time.sleep(2)  # respira entre tentativas

    return "[análise indisponível]"


def analise_video(frames: list[str], frames_dir: str) -> str:
    # Amostra frames distribuídos pelo vídeo — 1 frame por chamada
    max_frames = 8
    if len(frames) > max_frames:
        step = len(frames) // max_frames
        sampled = frames[::step][:max_frames]
    else:
        sampled = frames

    total = len(sampled)
    print(f"Analisando {total} frames (1 por chamada)...")

    analises = []
    for i, frame_name in enumerate(sampled, start=1):
        frame_path = os.path.join(frames_dir, frame_name)
        print(f"  Frame {i}/{total}: {frame_name}")
        resultado = analise_frame(frame_path, i, total)
        analises.append(f"[Frame {i}] {resultado}")
        time.sleep(1)  # pequena pausa entre frames para estabilizar VRAM

    return "\n\n".join(analises)


def decidir_trecho(analise: str, duracao_total: float) -> dict:
    """Chamada 2 — decide o trecho com base na análise anterior"""
    response = ollama.chat(
        model="qwen3-vl:8b",
        stream=False,
        messages=[
            {
                "role": "system",
                "content": "Você é um editor de vídeo especializado em clipes de academia. "
                "Responda APENAS com JSON válido, sem texto antes ou depois.",
            },
            {
                "role": "user",
                "content": f"""
Com base nesta análise de frames de um vídeo de {duracao_total:.1f} segundos:

{analise}

Escolha o melhor trecho de 20 a 45 segundos para um clipe de academia estilo TikTok.
Priorize: alta intensidade, boa composição visual, movimento expressivo.

Retorne APENAS este JSON:
{{
  "start_time": <float>,
  "end_time": <float>,
  "reason": "<motivo em uma frase>"
}}
""",
            },
        ],
        options={
            "temperature": 0.1,
            "num_predict": 256,
        },
    )
    return response.message.content
