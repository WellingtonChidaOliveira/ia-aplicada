import os
import subprocess
import textwrap

from utils.config import Config

FONT_PATH = "/home/wchida/.local/share/fonts/BebasNeue-Regular.ttf"


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


def _build_ffmpeg_command(
    video_path: str,
    start_time: float,
    duration: float,
    text_file_path: str,
    output_path: str,
    params: dict,
) -> str:
    """Monta o comando FFmpeg a partir dos parâmetros — sem LLM."""
    blur_dur = params["blur_duration"] if params["blur_duration"] > 1.5 else 1.5
    fade_dur = 0.6
    teal = params["teal_intensity"]

    dark = (
        f"scale=1080:1920:force_original_aspect_ratio=increase,"
        f"crop=1080:1920,"
        f"eq=brightness={params['brightness']}:contrast={params['contrast']}:"
        f"saturation={params['saturation']}:gamma={params['gamma']},"
        f"curves=r='0/0 0.5/0.38 1/0.85':g='0/0 0.5/0.40 1/0.88':b='0/0.04 0.5/0.48 1/0.95',"
        f"colorbalance=rs={-teal}:gs=0.0:bs={teal}:rm=-0.1:gm=0.0:bm=0.05,"
        f"eq=contrast=1.35:saturation=0.55:brightness=0.0,"
        f"vignette=angle={params['vignette_angle']}:mode=forward"
    )

    drawtext = (
        f"drawtext=textfile='{os.path.abspath(text_file_path)}'"
        f":fontfile='{FONT_PATH}'"
        f":fontsize={params['fontsize']}"
        f":fontcolor=white@0.95"
        f":bordercolor=black:borderw=2"
        f":shadowcolor=black@0.8:shadowx=4:shadowy=4"
        f":line_spacing=12:text_align=center"
        f":x=(w-text_w)/2:y={params['text_y']}"
    )

    filter_complex = (
        f"[0:v]trim=start=0:end={blur_dur:.1f},setpts=PTS-STARTPTS,"
        f"{dark},boxblur=15:15,"
        f"fade=t=out:st={blur_dur - fade_dur:.2f}:d={fade_dur}[blurred];"
        f"[0:v]trim=start={blur_dur:.1f},setpts=PTS-STARTPTS,"
        f"{dark},{drawtext},"
        f"fade=t=in:st=0:d={fade_dur}[sharp];"
        f"[blurred][sharp]concat=n=2:v=1:a=0[vout]"
    )

    return (
        f"ffmpeg -ss {start_time} -t {duration} -i '{video_path}' "
        f'-filter_complex "{filter_complex}" '
        f"-map '[vout]' -map 0:a? "
        f"-c:v libx264 -profile:v high -level:v 4.1 -pix_fmt yuv420p "
        f"-crf {Config.VIDEO_CRF} -preset {Config.VIDEO_PRESET} "
        f"-c:a aac -b:a {Config.VIDEO_AUDIO_BITRATE} -movflags +faststart "
        f"'{output_path}' -y"
    )


def _generate_and_execute(
    video_path: str,
    start_time: float,
    duration: float,
    text_file_path: str,
    rank: int,
    output_path: str,
    params: dict,
) -> dict:
    """Monta o comando FFmpeg com os parâmetros fornecidos e executa."""
    print(f"  Parâmetros (rank {rank}): brightness={params['brightness']} contrast={params['contrast']}")

    command = _build_ffmpeg_command(
        video_path, start_time, duration, text_file_path, output_path, params
    )
    print(f"  Comando FFmpeg:\n{command[:300]}...")

    print("  Executando FFmpeg...")
    try:
        result = subprocess.run(
            command,
            shell=True,
            check=True,
            capture_output=True,
            text=True,
        )

        if not os.path.exists(output_path) or os.path.getsize(output_path) == 0:
            return {"success": False, "output_path": "", "error": "Arquivo não gerado"}

        size_mb = os.path.getsize(output_path) / (1024 * 1024)
        print(f"  ✓ Clip gerado: {size_mb:.1f}MB → {output_path}")
        return {"success": True, "output_path": output_path, "error": ""}

    except subprocess.CalledProcessError as e:
        print(f"  FFmpeg erro:\n{e.stderr[-500:] if e.stderr else str(e)}")
        return {"success": False, "output_path": "", "error": e.stderr[-300:] if e.stderr else str(e)}
