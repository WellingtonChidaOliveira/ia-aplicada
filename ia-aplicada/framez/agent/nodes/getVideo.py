import json
import subprocess
from datetime import datetime
from models.GraphMessage import GraphMessage


def get_video_info(path: str) -> dict:
    cmd = [
        "ffprobe",
        "-v",
        "quiet",
        "-show_format",
        "-show_streams",
        "-print_format",
        "json",
        path,
    ]
    out = subprocess.run(cmd, capture_output=True, text=True)
    return json.loads(out.stdout)


def get_video_frames(path: str) -> GraphMessage:
    data = get_video_info(path)
    # Extract duration
    duration = float(data["format"]["duration"])
    # Extract framerate and total frames from first video stream
    total_frames = 0
    for stream in data["streams"]:
        if stream["codec_type"] == "video":
            # FPS
            fps_fraction = stream.get("avg_frame_rate", "0/1")
            num, den = map(int, fps_fraction.split("/"))
            fps = num / den if den != 0 else 0
            
            # Total frames
            nb_frames = stream.get("nb_frames")
            if nb_frames:
                total_frames = int(nb_frames)
            else:
                total_frames = int(duration * fps)
            break

    print(f"Vídeo carregado: {duration:.2f}s, {fps:.2f} fps, {total_frames} frames totais")

    return GraphMessage(
        datetime=datetime.now().isoformat(),
        video_path=path,
        success=True,
        error="",
        attempt=1,
        # video_info=data,
        duration=duration,
        fps=fps,
        total_frames=total_frames,
    )
