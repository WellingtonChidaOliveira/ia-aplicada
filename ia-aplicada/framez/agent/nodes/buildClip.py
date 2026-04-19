import subprocess
import os
import time
import textwrap
from models.GraphMessage import GraphMessage
from agent.prompts.v1.generatePhrase import generate_phrase_prompt
from service.llmRouter import LLMClient
from config.config import Config


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
            style="D",
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
        response = client.llm_router(
            generate_phrase_prompt(), model=Config.MODEL_LLM_PHRASE
        )
        return response.strip()
    except Exception as e:
        print(f"   Falha ao gerar frase: {e}")
        return "O peso que carregas é a prova de que ainda és real."


def _build_filtro_c(text_file_path: str, duration: float) -> str:
    fade_duration = 0.6

    filtros = [
        # 1. corte vertical
        "scale=1080:1920:force_original_aspect_ratio=increase",
        "crop=1080:1920",
        # 2. filtro dark Knight
        "eq=brightness=-0.15:contrast=1.0:saturation=0.5:gamma=0.85",
        "curves=r='0/0 0.5/0.38 1/0.85':g='0/0 0.5/0.40 1/0.88':b='0/0.04 0.5/0.48 1/0.95'",
        "colorbalance=rs=-0.25:gs=0.0:bs=0.15:rm=-0.1:gm=0.0:bm=0.05",
        "eq=contrast=1.35:saturation=0.55:brightness=0.0",
        "vignette=angle=PI/4:mode=forward",
    ]

    return ",".join(filtros)


def _build_filter_complex_c(text_file_path: str, duration: float) -> str:
    """Opção C: gradiente escuro na base + texto integrado."""
    fade_duration = 0.6
    # gradiente ocupa 40% inferior da tela (768px de 1920)
    gradient_height = 768

    return (
        # processa o vídeo com filtro dark
        f"[1:v]"
        f"scale=1080:1920:force_original_aspect_ratio=increase,"
        f"crop=1080:1920,"
        f"eq=brightness=-0.15:contrast=1.0:saturation=0.5:gamma=0.85,"
        f"curves=r='0/0 0.5/0.38 1/0.85':g='0/0 0.5/0.40 1/0.88':b='0/0.04 0.5/0.48 1/0.95',"
        f"colorbalance=rs=-0.25:gs=0.0:bs=0.15:rm=-0.1:gm=0.0:bm=0.05,"
        f"eq=contrast=1.35:saturation=0.55:brightness=0.0,"
        f"vignette=angle=PI/4:mode=forward"
        f"[vid];"
        # gera gradiente preto transparente → preto sólido de baixo para cima
        f"color=c=black:size=1080x{gradient_height}:rate=30[grad_base];"
        f"[grad_base]"
        f"geq=r=0:g=0:b=0:a='255*((Y)/{gradient_height})',"
        f"format=yuva420p"
        f"[grad];"
        # posiciona o gradiente na base do vídeo
        f"[vid][grad]overlay=x=0:y=1920-{gradient_height}[vid_grad];"
        # adiciona o texto sobre o gradiente
        f"[vid_grad]"
        f"drawtext=textfile='{text_file_path}'"
        f":fontsize=64"
        f":fontcolor=white@0.95"
        f":bordercolor=black:borderw=2"
        f":shadowcolor=black@0.8:shadowx=2:shadowy=2"
        f":line_spacing=20"
        f":text_align=center"
        f":x=(w-text_w)/2"
        f":y=h*0.72"
        f":alpha='if(lt(t\\,0.8)\\,t/0.8\\,if(gt(t\\,{duration - 0.8:.2f})\\,({duration:.2f}-t)/0.8\\,1))'"
        f"[vout]"
    )


def _render_clip(
    video_path: str,
    start_time: float,
    duration: float,
    phrase: str,
    output_path: str,
    output_dir: str,
    base_timestamp: int,
    rank: int,
    style: str = "A",  # "A" = intro preta | "C" = gradiente
) -> dict:
    raw_phrase = phrase.replace("'", "").replace('"', "")
    wrapped_lines = textwrap.wrap(raw_phrase, width=27)
    text_file_path = os.path.join(output_dir, f"{base_timestamp}_top{rank}_text.txt")

    with open(text_file_path, "w", encoding="utf-8") as f:
        f.write("\n".join(wrapped_lines))

    if style == "A":
        intro_duration = 3.0
        fade_duration = 0.6

        filter_complex = (
            f"[0:v]"
            f"drawtext=textfile='{text_file_path}'"
            f":fontsize=64:fontcolor=white@0.95"
            f":bordercolor=black:borderw=3"
            f":shadowcolor=black@0.9:shadowx=2:shadowy=2"
            f":line_spacing=20:text_align=center"
            f":x=(w-text_w)/2:y=(h-text_h)/2"
            f":alpha='if(lt(t\\,0.8)\\,t/0.8\\,if(gt(t\\,{intro_duration - 0.8:.2f})\\,({intro_duration:.2f}-t)/0.8\\,1))',"
            f"fade=t=out:st={intro_duration - fade_duration:.2f}:d={fade_duration}"
            f"[intro];"
            f"[1:v]"
            f"scale=1080:1920:force_original_aspect_ratio=increase,"
            f"crop=1080:1920,"
            f"eq=brightness=-0.15:contrast=1.0:saturation=0.5:gamma=0.85,"
            f"curves=r='0/0 0.5/0.38 1/0.85':g='0/0 0.5/0.40 1/0.88':b='0/0.04 0.5/0.48 1/0.95',"
            f"colorbalance=rs=-0.25:gs=0.0:bs=0.15:rm=-0.1:gm=0.0:bm=0.05,"
            f"eq=contrast=1.35:saturation=0.55:brightness=0.0,"
            f"vignette=angle=PI/4:mode=forward,"
            f"fade=t=in:st=0:d={fade_duration}"
            f"[vid];"
            f"[intro][vid]concat=n=2:v=1:a=0[vout]"
        )

        cmd = [
            "ffmpeg",
            "-f",
            "lavfi",
            "-i",
            f"color=c=black:size=1080x1920:rate=30:duration={intro_duration}",
            "-ss",
            str(start_time),
            "-i",
            video_path,
            "-t",
            str(duration),
            "-filter_complex",
            filter_complex,
            "-map",
            "[vout]",
            "-map",
            "1:a?",
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
    elif style == "D":
        # texto aparece após 1.5s do vídeo já rodando
        text_start = 1.5
        fade_duration = 0.8

        filter_complex = (
            f"[0:v]"
            f"scale=1080:1920:force_original_aspect_ratio=increase,"
            f"crop=1080:1920,"
            f"eq=brightness=-0.15:contrast=1.0:saturation=0.5:gamma=0.85,"
            f"curves=r='0/0 0.5/0.38 1/0.85':g='0/0 0.5/0.40 1/0.88':b='0/0.04 0.5/0.48 1/0.95',"
            f"colorbalance=rs=-0.25:gs=0.0:bs=0.15:rm=-0.1:gm=0.0:bm=0.05,"
            f"eq=contrast=1.35:saturation=0.55:brightness=0.0,"
            f"vignette=angle=PI/4:mode=forward,"
            f"drawtext=textfile='{text_file_path}'"
            f":fontsize=64"
            f":fontcolor=white@0.95"
            f":bordercolor=black:borderw=3"
            f":shadowcolor=black@0.95:shadowx=3:shadowy=3"
            f":line_spacing=20"
            f":text_align=center"
            f":x=(w-text_w)/2"
            f":y=(h-text_h)*0.72"
            # aparece após text_start segundos, some nos últimos 0.8s
            f":enable='gte(t\\,{text_start})'"
            f":alpha='if(lt(t\\,{text_start + fade_duration:.2f})\\,"
            f"(t-{text_start:.2f})/{fade_duration}\\,"
            f"if(gt(t\\,{duration - fade_duration:.2f})\\,"
            f"({duration:.2f}-t)/{fade_duration}\\,1))'"
            f"[vout]"
        )

        cmd = [
            "ffmpeg",
            "-ss",
            str(start_time),
            "-i",
            video_path,
            "-t",
            str(duration),
            "-filter_complex",
            filter_complex,
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

    else:  # style == "C"
        gradient_height = 768

        filter_complex = _build_filter_complex_c(text_file_path, duration)

        cmd = [
            "ffmpeg",
            "-f",
            "lavfi",
            "-i",
            f"color=c=black:size=1080x{gradient_height}:rate=30",
            "-ss",
            str(start_time),
            "-i",
            video_path,
            "-t",
            str(duration),
            "-filter_complex",
            filter_complex,
            "-map",
            "[vout]",
            "-map",
            "1:a?",
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
