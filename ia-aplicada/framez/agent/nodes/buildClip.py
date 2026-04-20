import subprocess
import os
import time
import textwrap
from models.GraphMessage import GraphMessage
from agent.prompts.v3.generatePhrase import generate_phrase_prompt
from service.llmRouter import LLMClient
from service.ollama import send_text_ollama
from utils.config import Config
from utils.filter_text import FilterText


def _gerar_frase(client: LLMClient) -> str:
    """Chama o LLM para gerar uma frase motivacional única."""
    try:
        # response = send_text_ollama(generate_phrase_prompt())
        response = client.llm_router(
            prompt=generate_phrase_prompt(),
            model=Config.MODEL_LLM_PHRASE,
            options={
                "temperature": 1.2,
                "top_p": 0.95,
                "frequency_penalty": 1.0,  # penaliza repetição de tokens
                "presence_penalty": 0.8,  # incentiva explorar novos temas
            },
        )
        return response.strip()
    except Exception as e:
        print(f"   Falha ao gerar frase: {e}")
        print("   Usando frase de fallback")
        response = send_text_ollama(generate_phrase_prompt())
        return response.strip()


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
    raw_phrase = phrase.replace("'", "").replace('"', "")
    wrapped_lines = textwrap.wrap(raw_phrase, width=27)
    text_file_path = os.path.join(output_dir, f"{base_timestamp}_top{rank}_text.txt")

    with open(text_file_path, "w", encoding="utf-8") as f:
        f.write("\n".join(wrapped_lines))

    filter = FilterText()
    cmd = [
        "ffmpeg",
        "-ss",
        str(start_time),
        "-i",
        video_path,
        "-t",
        str(duration),
        "-filter_complex",
        filter.filter_complex(text_file_path, duration),
        "-map",
        "[vout]",
        "-map",
        "0:a?",
        "-c:v",
        "libx264",
        "-preset",
        "fast",
        "-crf",
        "23",
        "-c:a",
        "aac",
        "-b:a",
        "128k",
        "-movflags",
        "+faststart",
        output_path,
        "-y",
    ]

    result = subprocess.run(cmd, capture_output=True, text=True)

    try:
        os.remove(text_file_path)
    except Exception:
        pass

    if result.returncode != 0:
        print(f"FFmpeg erro:\n{result.stderr[-1000:]}")
        return {"success": False, "error": result.stderr[-500:]}

    if not os.path.exists(output_path) or os.path.getsize(output_path) == 0:
        return {"success": False, "error": "Arquivo não gerado"}

    return {"success": True, "error": ""}
