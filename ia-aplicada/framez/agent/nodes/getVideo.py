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
    fps = 0

    # Extract framerate from first video stream
    for stream in data["streams"]:
        if stream["codec_type"] == "video":
            fps_fraction = stream["avg_frame_rate"]
            num, den = map(int, fps_fraction.split("/"))
            fps = num / den
            break

    return GraphMessage(
        datetime=datetime.now().isoformat(),
        video_path=path,
        success=True,
        error="",
        attempt=1,
        # video_info=data,
        duration=duration,
        fps=fps,
    )
