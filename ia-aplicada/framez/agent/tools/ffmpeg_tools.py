import os
import re
import subprocess
import textwrap
from langchain.tools import tool
from utils.config import Config

FONT_PATH = "/home/wchida/.local/share/fonts/BebasNeue-Regular.ttf"

# Exemplo concreto que será injetado no prompt com paths reais
FFMPEG_EXAMPLE_TEMPLATE = """ffmpeg -ss {{start_time}} -t {{duration}} -i '{{video_path}}' -filter_complex "[0:v]trim=start=0:end=2.5,setpts=PTS-STARTPTS,scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,eq=brightness=-0.15:contrast=1.0:saturation=0.5:gamma=0.85,curves=r='0/0 0.5/0.38 1/0.85':g='0/0 0.5/0.40 1/0.88':b='0/0.04 0.5/0.48 1/0.95',colorbalance=rs=-0.25:gs=0.0:bs=0.15:rm=-0.1:gm=0.0:bm=0.05,eq=contrast=1.35:saturation=0.55:brightness=0.0,vignette=angle=PI/4:mode=forward,boxblur=15:15,fade=t=out:st=1.9:d=0.6[blurred];[0:v]trim=start=2.5,setpts=PTS-STARTPTS,scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,eq=brightness=-0.15:contrast=1.0:saturation=0.5:gamma=0.85,curves=r='0/0 0.5/0.38 1/0.85':g='0/0 0.5/0.40 1/0.88':b='0/0.04 0.5/0.48 1/0.95',colorbalance=rs=-0.25:gs=0.0:bs=0.15:rm=-0.1:gm=0.0:bm=0.05,eq=contrast=1.35:saturation=0.55:brightness=0.0,vignette=angle=PI/4:mode=forward,drawtext=textfile='{{text_file}}':fontfile='{{font_path}}':fontsize=72:fontcolor=white@0.95:bordercolor=black:borderw=2:shadowcolor=black@0.8:shadowx=4:shadowy=4:line_spacing=12:text_align=center:x=(w-text_w)/2:y=h*0.78,fade=t=in:st=0:d=0.6[sharp];[blurred][sharp]concat=n=2:v=1:a=0[vout]" -map '[vout]' -map 0:a? -c:v libx264 -profile:v high -level:v 4.1 -pix_fmt yuv420p -crf 23 -preset fast -c:a aac -b:a 128k -movflags +faststart '{{output_path}}' -y"""

# ── FUNÇÕES INTERNAS (sem @tool) ─────────────────────────────────────────────


def _prepare_text_file(phrase: str, output_dir: str, base_timestamp: int) -> str:
    """Cria arquivo de texto com a frase para o drawtext do FFmpeg."""
    raw_phrase = phrase.replace("'", "").replace('"', "")
    wrapped_lines = textwrap.wrap(
        raw_phrase, width=22, break_long_words=False, break_on_hyphens=False
    )
    abs_output_dir = os.path.abspath(output_dir)
    text_file_path = os.path.join(abs_output_dir, f"{base_timestamp}_text.txt")
    with open(text_file_path, "w", encoding="utf-8") as f:
        f.write("\n".join(wrapped_lines))
    return text_file_path


def _fix_ffmpeg_command(
    command: str, text_file_path: str | None, output_path: str
) -> str:
    """Corrige erros comuns gerados pelo LLM no comando FFmpeg."""
    # ── limpeza básica ───────────────────────────────────────────────────
    # remove markdown code blocks
    command = re.sub(r"`{3}[a-zA-Z]*\s*", "", command)
    command = re.sub(r"`{3}\s*", "", command)
    command = command.strip()

    # remove newlines internos
    command = re.sub(r"\n\s*", " ", command)
    command = command.strip()

    # remove chaves soltas que o LLM às vezes insere
    command = re.sub(r"\},", ",", command)
    command = re.sub(r"\{(\w)", r"\1", command)
    command = re.sub(r"(\w)\}", r"\1", command)

    # garante que começa com ffmpeg
    if not command.startswith("ffmpeg"):
        idx = command.find("ffmpeg")
        if idx != -1:
            command = command[idx:]

    # ── typos de nomes de filtros ────────────────────────────────────────
    # LLM gerou "drawwtext" (2 w's) — corrige para "drawtext"
    command = re.sub(r"\bdraww+text\b", "drawtext", command)
    # outros typos comuns
    command = re.sub(r"\bdarwtext\b", "drawtext", command)
    command = re.sub(r"\bdrawttext\b", "drawtext", command)

    # ── -vf → -filter_complex (quando usa stream labels [0:v]) ──────────
    command = re.sub(r"\s+-vf\s+", " -filter_complex ", command)

    # ── drawtext solto: merge na chain do [sharp] ────────────────────────
    # O LLM às vezes gera ";drawtext=..." como segmento separado em vez de
    # encadear na chain do [sharp]. Isso causa:
    # "Cannot find an unused video input stream to feed unlabeled input pad"
    # Solução: remove o ";drawtext" solto e garante que está na chain [sharp]
    command = re.sub(r";\s*drawtext=", ",drawtext=", command)

    # ── corrige parâmetros drawtext com : em vez de = ────────────────────
    drawtext_params = [
        "fontsize", "fontcolor", "bordercolor", "borderw",
        "shadowcolor", "shadowx", "shadowy", "line_spacing",
        "text_align", "x", "y", "alpha", "fontfile", "textfile",
        "font", "box", "boxcolor", "boxborderw",
    ]
    for param in drawtext_params:
        command = re.sub(rf"\b({param}):", rf"\1=", command)
    command = re.sub(r"text_align:(\w+)", r"text_align=\1", command)

    # ── substitui placeholder DRAWTEXT_HERE pelo drawtext real ───────────
    if "DRAW_TEXT_HERE" in command or "DRAWTEXT_HERE" in command:
        abs_text = os.path.abspath(text_file_path) if text_file_path else ""
        real_drawtext = (
            f"drawtext=textfile='{abs_text}'"
            f":fontfile='{FONT_PATH}'"
            f":fontsize=72"
            f":fontcolor=white@0.95"
            f":bordercolor=black:borderw=2"
            f":shadowcolor=black@0.8:shadowx=4:shadowy=4"
            f":line_spacing=12:text_align=center"
            f":x=(w-text_w)/2:y=h*0.78"
        )
        command = command.replace("DRAW_TEXT_HERE", real_drawtext)
        command = command.replace("DRAWTEXT_HERE", real_drawtext)

    # ── vignette: remove parâmetros inválidos ────────────────────────────
    _vignette_valid = {"angle", "a", "x0", "y0", "mode", "eval", "dither", "aspect"}

    def _clean_vignette(m):
        params_str = m.group(1)
        parts = re.split(r"(?<!=):(?!=)", params_str)
        valid_parts = []
        for part in parts:
            key = part.split("=")[0].strip()
            if key in _vignette_valid:
                valid_parts.append(part.strip())
        if valid_parts:
            return "vignette=" + ":".join(valid_parts)
        return "vignette=angle=PI/4:mode=forward"

    command = re.sub(r"vignette=([^,\[\];]+)", _clean_vignette, command)

    # ── eq: remove parâmetros inválidos ──────────────────────────────────
    _eq_valid = {
        "brightness", "contrast", "saturation", "gamma",
        "gamma_r", "gamma_g", "gamma_b", "gamma_weight", "eval",
    }

    def _clean_eq(m):
        params_str = m.group(1)
        parts = params_str.split(":")
        valid_parts = []
        for part in parts:
            key = part.split("=")[0].strip()
            if key in _eq_valid:
                valid_parts.append(part.strip())
        if valid_parts:
            return "eq=" + ":".join(valid_parts)
        return "eq=brightness=-0.15:contrast=1.0:saturation=0.5"

    command = re.sub(r"eq=([^,\[\];]+)", _clean_eq, command)

    # ── garante -map '[vout]' para o filter_complex ───────────────────────
    if "[vout]" in command and "-map" not in command:
        # insere -map antes do codec
        command = re.sub(
            r"(-c:v\s)",
            r"-map '[vout]' -map 0:a? \1",
            command,
            count=1,
        )
    elif "-map 0:a" not in command and '-map "0:a' not in command:
        abs_output = os.path.abspath(output_path)
        command = command.replace(f" {abs_output}", f" -map 0:a? {abs_output}")
        command = command.replace(f" {output_path}", f" -map 0:a? {output_path}")

    # ── força path correto do textfile ───────────────────────────────────
    if text_file_path:
        abs_text = os.path.abspath(text_file_path)
        command = re.sub(r"textfile='[^']*'", f"textfile='{abs_text}'", command)
        command = re.sub(r"textfile=[^\s:,\]]+", f"textfile='{abs_text}'", command)

    # ── força path correto do fontfile ───────────────────────────────────
    command = re.sub(r"fontfile='[^']*'", f"fontfile='{FONT_PATH}'", command)
    command = re.sub(r"fontfile=[^\s:,\]]+", f"fontfile='{FONT_PATH}'", command)

    # ── shell escaping: garante que -filter_complex está entre aspas ─────
    # Parênteses como x=(w-text_w)/2 causam "Syntax error: '(' unexpected"
    # se o valor do -filter_complex não estiver entre aspas duplas
    fc_match = re.search(r'-filter_complex\s+(".*?"|\'.*?\'|\S+)', command)
    if fc_match:
        fc_value = fc_match.group(1)
        # se não começa com aspas, envolve com aspas duplas
        if not fc_value.startswith('"') and not fc_value.startswith("'"):
            command = command.replace(
                f"-filter_complex {fc_value}",
                f'-filter_complex "{fc_value}"',
            )

    return command


def _validate_ffmpeg_command(command: str, expected_output: str) -> str:
    """Valida o comando FFmpeg antes de executar. Retorna string de erro ou vazio."""
    if not command.strip().startswith("ffmpeg"):
        return "Command must start with 'ffmpeg'"

    # remove conteúdo entre aspas antes de checar injection
    command_without_quotes = re.sub(r"'[^']*'", "", command)
    dangerous = ["&&", "||", "`", "$(", "${"]
    for char in dangerous:
        if char in command_without_quotes:
            return f"Dangerous character found: {char}"

    network_flags = ["rtmp://", "udp://", "tcp://"]
    for flag in network_flags:
        if flag in command:
            return f"Network flag not allowed: {flag}"

    if " -i " not in command:
        return "Missing input flag -i"

    if expected_output not in command:
        return f"Expected output path not found: {expected_output}"

    return ""


def _generate_ffmpeg_command_internal(
    video_path: str,
    start_time: float,
    duration: float,
    text_file_path: str,
    phrase: str,
    rank: int,
    output_path: str,
    style_hint: str = "dark cinematic gym",
) -> str:
    """Gera comando FFmpeg via LLM — versão interna sem @tool."""
    from service.llm_router import LLMClient

    client = LLMClient()

    # monta exemplo concreto com os paths reais
    example = FFMPEG_EXAMPLE_TEMPLATE.replace("{{start_time}}", str(start_time))
    example = example.replace("{{duration}}", str(duration))
    example = example.replace("{{video_path}}", video_path)
    example = example.replace("{{text_file}}", os.path.abspath(text_file_path))
    example = example.replace("{{font_path}}", FONT_PATH)
    example = example.replace("{{output_path}}", output_path)

    prompt = f"""You are an FFmpeg expert. Generate a complete ffmpeg command.

Here is a WORKING EXAMPLE with the exact structure you must follow:
{example}

You MUST keep this EXACT structure:
1. -ss and -t BEFORE -i
2. -filter_complex with exactly this pattern:
   [0:v]trim...DARK_FILTERS,boxblur,fade[blurred];
   [0:v]trim...DARK_FILTERS,drawtext=...,fade[sharp];
   [blurred][sharp]concat=n=2:v=1:a=0[vout]
3. drawtext MUST be chained with comma inside the [sharp] segment, NEVER as a separate ;drawtext segment
4. -map '[vout]' -map 0:a? after the filter_complex
5. codec flags, then output path, then -y

You CAN vary these parameters creatively (rank {rank}/3):
- eq brightness (-0.05 to -0.25), contrast (0.9 to 1.5), saturation (0.3 to 0.7), gamma (0.75 to 0.95)
- colorbalance rs/gs/bs/rm/gm/bm values
- curves control points
- vignette angle (PI/3 to PI/6) — ONLY params: angle, x0, y0, mode
- boxblur radius (10 to 20)
- drawtext fontsize (60 to 84), y position
- blur duration (1.5 to 3.5 seconds)

Do NOT change: scale, crop, codec settings, drawtext textfile/fontfile paths.
Return ONLY the ffmpeg command. No markdown, no explanation, no code blocks."""

    response = client.llm_router(
        prompt=prompt,
        model="openai/gpt-4o-mini",
        options={"temperature": 0.7},
    )
    command = response.strip()
    print(f"  Comando gerado pelo LLM (rank {rank}):\n{command[:200]}...")
    return command


def _execute_ffmpeg_internal(
    command: str,
    output_path: str,
    text_file_path: str | None,
) -> dict:
    """Executa comando FFmpeg — versão interna sem @tool."""
    command = _fix_ffmpeg_command(command, text_file_path, output_path)
    print(f"  Comando após limpeza:\n{command[:300]}...")

    validation_error = _validate_ffmpeg_command(command, output_path)
    if validation_error:
        print(f"  Comando inválido: {validation_error}")
        return {"success": False, "error": validation_error, "output_path": ""}

    print("  Executando FFmpeg...")
    result = subprocess.run(command, shell=True, capture_output=True, text=True)

    if result.returncode != 0:
        print(f"  FFmpeg erro:\n{result.stderr[-500:]}")
        return {"success": False, "error": result.stderr[-300:], "output_path": ""}

    if not os.path.exists(output_path) or os.path.getsize(output_path) == 0:
        return {"success": False, "error": "Arquivo não gerado", "output_path": ""}

    size_mb = os.path.getsize(output_path) / (1024 * 1024)
    print(f"  ✓ Clip gerado: {size_mb:.1f}MB → {output_path}")
    return {"success": True, "output_path": output_path, "error": ""}


# ── TOOLS EXPOSTAS AO AGENTE (@tool) ─────────────────────────────────────────


@tool
def generate_ffmpeg_command(
    video_path: str,
    start_time: float,
    duration: float,
    text_file_path: str,
    phrase: str,
    rank: int,
    output_path: str,
    style_hint: str = "dark cinematic gym",
) -> str:
    """
    Generates a complete FFmpeg command for rendering a dark gym clip.
    Used internally by build_clip.
    """
    return _generate_ffmpeg_command_internal(
        video_path,
        start_time,
        duration,
        text_file_path,
        phrase,
        rank,
        output_path,
        style_hint,
    )


@tool
def execute_ffmpeg(command: str, output_path: str, text_file_path: str) -> dict:
    """
    Validates and executes an FFmpeg command.
    Used internally by build_clip.
    """
    return _execute_ffmpeg_internal(command, output_path, text_file_path)
