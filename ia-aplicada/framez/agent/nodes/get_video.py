import json
import subprocess
from datetime import datetime
from models.graph_message import GraphMessage


class VideoInfo:
    def __init__(self, path: str):
        self.path = path
        self.data = self.get_video_info()
        self._parse_metadata()

    def get_video_info(self) -> dict:
        cmd = [
            "ffprobe",
            "-v",
            "quiet",
            "-show_format",
            "-show_streams",
            "-print_format",
            "json",
            self.path,
        ]
        out = subprocess.run(cmd, capture_output=True, text=True)
        try:
            return json.loads(out.stdout)
        except json.JSONDecodeError:
            return {}

    def _parse_metadata(self):
        # Extract duration
        format_data = self.data.get("format", {})
        self.duration = float(format_data.get("duration", 0))

        # Extract framerate and total frames from first video stream
        self.fps = 0
        self.total_frames = 0
        for stream in self.data.get("streams", []):
            if stream.get("codec_type") == "video":
                # FPS
                fps_fraction = stream.get("avg_frame_rate", "0/1")
                try:
                    num, den = map(int, fps_fraction.split("/"))
                    self.fps = num / den if den != 0 else 0
                except (ValueError, ZeroDivisionError):
                    self.fps = 0

                # Total frames
                nb_frames = stream.get("nb_frames")
                if nb_frames:
                    self.total_frames = int(nb_frames)
                else:
                    self.total_frames = int(self.duration * self.fps)
                break

    def get_video_frames(self, state: GraphMessage) -> dict:
        print(
            f"Vídeo carregado: {self.duration:.2f}s, {self.fps:.2f} fps, {self.total_frames} frames totais"
        )

        return {
            "datetime": datetime.now().isoformat(),
            "video_path": self.path,
            "success": True,
            "error": "",
            "attempt": 1,
            "duration": self.duration,
            "fps": self.fps,
            "total_frames": self.total_frames,
        }

