import json
import os
import subprocess
from datetime import datetime

from utils import helper
from langchain.tools import tool


@tool
def get_video_info(path: str) -> dict:
    """
    Retrieves video duration, FPS, and total frames using ffprobe.
    Requires state containing the 'video_path'.
    """
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
    try:
        data = json.loads(out.stdout)
    except json.JSONDecodeError:
        data = {}

    duration = float(data["format"]["duration"])

    fps = 0
    total_frames = 0
    for stream in data["streams"]:
        if stream["codec_type"] == "video":
            fps_fraction = stream["avg_frame_rate"]
            try:
                num, den = map(int, fps_fraction.split("/"))
                fps = num / den if den != 0 else 0
            except (ValueError, ZeroDivisionError):
                fps = 0

            total_frames = (
                int(stream["nb_frames"]) if stream["nb_frames"] else int(duration * fps)
            )
            break

    print(
        f"Vídeo carregado: {duration:.2f}s, {fps:.2f} fps, {total_frames} frames totais"
    )

    return {
        "datetime": datetime.now().isoformat(),
        "video_path": path,
        "success": True,
        "error": "",
        "attempt": 1,
        "duration": duration,
        "fps": fps,
        "total_frames": total_frames,
    }


@tool
def extract_frames(video_path: str, duration: float) -> dict[str, str | list[str]]:
    """Extracts frames from the video at regular intervals"""
    frames_dir = f"./tmp/gym_frames_{os.getpid()}"
    os.makedirs(frames_dir, exist_ok=True)

    max_frames = helper.calculate_max_frames(duration)

    start = 2.0
    end = duration - 2.0

    interval = (end - start) / (max_frames - 1)
    timestamps = [start + i * interval for i in range(max_frames)]

    frames = []
    for i, t in enumerate(timestamps, start=1):
        filename = f"frame_{i:04d}_t{t:07.2f}.jpg"
        output_path = os.path.join(frames_dir, filename)

        cmd = [
            "ffmpeg",
            "-ss",
            str(t),
            "-i",
            video_path,
            "-vframes",
            "1",
            "-vf",
            "scale='min(1280,iw)':'min(720,ih)':force_original_aspect_ratio=decrease",
            "-q:v",
            "2",
            output_path,
            "-y",
        ]

        subprocess.run(cmd, capture_output=True)

        if os.path.exists(output_path):
            frames.append(filename)
            print(f"  Frame {i}/{max_frames} extracted: t={t:.2f}s")
        else:
            print(f"  Frame {i}/{max_frames} failed: t={t:.2f}s")

    print(f"Frames extracted: {len(frames)}/{max_frames}")
    print(f"Frames dir: {frames_dir}")

    return {"frames_dir": frames_dir, "frames": frames}
