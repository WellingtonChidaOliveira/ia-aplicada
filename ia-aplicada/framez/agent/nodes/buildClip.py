import subprocess
import os
import time
import textwrap
from models.GraphMessage import GraphMessage


def build_clip(state: GraphMessage) -> GraphMessage:
    output_dir = "output"
    os.makedirs(output_dir, exist_ok=True)

    # nome do arquivo de saída
    video_name = os.path.splitext(os.path.basename(state.get("video_path")))[0]
    timestamp = int(time.time())
    output_path = os.path.join(output_dir, f"{timestamp}_{video_name}_dark.mp4")

    duration = state.get("end_time") - state.get("start_time")
    raw_phrase = state.get("motivation_phrase").replace("'", "").replace('"', "")

    # quebra a frase para ficar com estilo de legenda (aprox 25 caracteres por linha)
    wrapped_lines = textwrap.wrap(raw_phrase, width=27)
    # salva texto num arquivo para evitar problemas de escape no ffmpeg
    text_file_path = os.path.join(output_dir, f"{timestamp}_text.txt")
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
        "-ss",
        str(state.get("start_time")),
        "-i",
        state.get("video_path"),
        "-t",
        str(duration),
        "-vf",
        filtro_video,
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

    print(
        f"Gerando clipe: {state.get('start_time'):.2f}s → {state.get('end_time'):.2f}s ({duration:.1f}s)"
    )
    print(f"Frase: {state.get('motivation_phrase')}")
    print(f"Output: {output_path}")

    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode != 0:
        print(f"FFmpeg erro:\n{result.stderr}")
        return {
            "success": False,
            "error": result.stderr[-500:],
            "output_path": "",
        }

    if not os.path.exists(output_path) or os.path.getsize(output_path) == 0:
        return {
            "success": False,
            "error": "Arquivo de saída não foi gerado",
            "output_path": "",
        }

    tamanho_mb = os.path.getsize(output_path) / (1024 * 1024)
    print(f"Clipe gerado com sucesso: {tamanho_mb:.1f}MB")

    if os.path.exists(text_file_path):
        try:
            os.remove(text_file_path)
        except Exception:
            pass

    return {
        "success": True,
        "output_path": output_path,
    }
