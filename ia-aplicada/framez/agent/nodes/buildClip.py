import subprocess
import os
import time
from models.GraphMessage import GraphMessage


def build_clip(state: GraphMessage) -> GraphMessage:
    output_dir = "output"
    os.makedirs(output_dir, exist_ok=True)

    # nome do arquivo de saída
    video_name = os.path.splitext(os.path.basename(state.get("video_path")))[0]
    timestamp = int(time.time())
    output_path = os.path.join(output_dir, f"{timestamp}_{video_name}_dark.mp4")

    duration = state.get("end_time") - state.get("start_time")
    phrase = state.get("motivation_phrase")

    # quebra a frase se for muito longa
    if len(phrase) > 40:
        meio = len(phrase) // 2
        espaco = phrase.rfind(" ", 0, meio)
        if espaco != -1:
            phrase = phrase[:espaco] + "\n" + phrase[espaco + 1 :]

    # tamanho da fonte proporcional ao comprimento
    font_size = 60 if len(state.get("motivation_phrase")) <= 30 else 48

    filtro_video = ",".join(
        [
            # 1. corte vertical com padding
            "scale=1080:1920:force_original_aspect_ratio=decrease",
            "pad=1080:1920:(ow-iw)/2:(oh-ih)/2:black",
            # 2. curva cinematográfica — levanta blacks, achata highlights
            "curves=all='0/15 0.85/220 1/235'",
            # 3. shift teal nas sombras
            "colorbalance=bs=-0.1:gs=0.05:rs=-0.15",
            # 4. contraste alto, saturação baixa
            "eq=contrast=1.4:saturation=0.65:brightness=-0.05",
            # 5. vinheta nas bordas
            "vignette=angle=PI/5",
            # 6. overlay da frase com fade in/out
            (
                f"drawtext=text='{phrase}'"
                f":fontsize={font_size}"
                f":fontcolor=white"
                f":bordercolor=black"
                f":borderw=4"
                f":x=(w-text_w)/2"
                f":y=h*0.80"
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

    return {
        "success": True,
        "output_path": output_path,
    }
