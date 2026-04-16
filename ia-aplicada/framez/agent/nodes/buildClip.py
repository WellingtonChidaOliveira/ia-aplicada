import subprocess
import os
import time
import textwrap
from models.GraphMessage import GraphMessage
from agent.prompts.v2.generatePhrase import generate_phrase_prompt
from service.llmRouter import LLMClient


def build_clip(state: GraphMessage, client: LLMClient) -> GraphMessage:
    output_dir = "output"
    os.makedirs(output_dir, exist_ok=True)

    segments = state.get("segments") or []
    video_name = os.path.splitext(os.path.basename(state.get("video_path")))[0]
    base_timestamp = int(time.time())

    output_paths = []
    errors = []

    for seg in segments:
        rank = seg.get("rank", len(output_paths) + 1)
        start_time = seg["start_time"]
        end_time = seg["end_time"]
        duration = end_time - start_time

        print(f"\n── Gerando clipe top{rank} ─────────────────────────────")
        print(f"   Trecho: {start_time:.2f}s → {end_time:.2f}s ({duration:.1f}s)")
        print(f"   Motivo: {seg.get('reason', '')}")

        # gera frase motivacional individual para este clipe
        phrase = _gerar_frase(client)
        print(f"   Frase: {phrase}")

        output_path = os.path.join(
            output_dir, f"{base_timestamp}_{video_name}_top{rank}.mp4"
        )

        result = _render_clip(
            video_path=state.get("video_path"),
            start_time=start_time,
            duration=duration,
            phrase=phrase,
            output_path=output_path,
            output_dir=output_dir,
            base_timestamp=base_timestamp,
            rank=rank,
        )

        if result["success"]:
            tamanho_mb = os.path.getsize(output_path) / (1024 * 1024)
            print(f"   ✓ Salvo em: {output_path} ({tamanho_mb:.1f}MB)")
            output_paths.append(output_path)
        else:
            print(f"   ✗ Erro no top{rank}: {result['error'][:200]}")
            errors.append(result["error"])

    print(f"\n══ {len(output_paths)}/3 clipes gerados com sucesso ══")

    return {
        "success": len(output_paths) > 0,
        "output_paths": output_paths,
        "output_path": output_paths[0] if output_paths else "",
        "error": "; ".join(errors) if errors else "",
    }


def _gerar_frase(client: LLMClient) -> str:
    """Chama o LLM para gerar uma frase motivacional única."""
    try:
        response = client.llm_router(generate_phrase_prompt())
        return response.strip()
    except Exception as e:
        print(f"   Falha ao gerar frase: {e}")
        return "O peso que carregas é a prova de que ainda és real."


def _render_clip(
    video_path: str,
    start_time: float,
    duration: float,
    phrase: str,
    output_path: str,
    output_dir: str,
    base_timestamp: int,
    rank: int,
) -> dict:
    """Monta e executa o comando FFmpeg para renderizar um único clipe."""
    raw_phrase = phrase.replace("'", "").replace('"', "")
    wrapped_lines = textwrap.wrap(raw_phrase, width=27)
    text_file_path = os.path.join(output_dir, f"{base_timestamp}_top{rank}_text.txt")

    with open(text_file_path, "w", encoding="utf-8") as f:
        f.write("\n".join(wrapped_lines))

    filtro_video = ",".join(
        [
            # 1. corte vertical (preenche tela e recorta as laterais)
            "scale=1080:1920:force_original_aspect_ratio=increase",
            "crop=1080:1920",
            # 2. curva cinematográfica — levanta blacks, achata highlights
            "curves=all='0/0.06 0.85/0.86 1/0.92'",
            # 3. shift teal nas sombras
            "colorbalance=bs=-0.1:gs=0.05:rs=-0.15",
            # 4. contraste alto, saturação baixa
            "eq=contrast=1.4:saturation=0.65:brightness=-0.05",
            # 5. vinheta nas bordas
            "vignette=angle=PI/5",
            # 6. overlay da frase com fade in/out + estilo dark (box, shadows)
            (
                f"drawtext=textfile='{text_file_path}'"
                f":fontsize=72"
                f":fontcolor=white"
                f":bordercolor=black:borderw=5"
                f":shadowcolor=black@0.9:shadowx=3:shadowy=3"
                f":line_spacing=16"
                f":x=(w-text_w)/2"
                f":y=(h-text_h)*0.75"
                f":alpha='if(lt(t,0.5),t/0.5,if(gt(t,{duration:.2f}-0.5),({duration:.2f}-t)/0.5,1))'"
            ),
        ]
    )

    cmd = [
        "ffmpeg",
        "-ss", str(start_time),
        "-i", video_path,
        "-t", str(duration),
        "-vf", filtro_video,
        "-c:v", "libx264",
        "-preset", "fast",
        "-crf", "23",
        "-c:a", "aac",
        "-b:a", "128k",
        "-movflags", "+faststart",
        output_path,
        "-y",
    ]

    result = subprocess.run(cmd, capture_output=True, text=True)

    # limpa arquivo de texto temporário
    try:
        os.remove(text_file_path)
    except Exception:
        pass

    if result.returncode != 0:
        return {"success": False, "error": result.stderr[-500:]}

    if not os.path.exists(output_path) or os.path.getsize(output_path) == 0:
        return {"success": False, "error": "Arquivo de saída não foi gerado"}

    return {"success": True, "error": ""}

