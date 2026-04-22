import subprocess
import os
from models.graph_message import GraphMessage


class ExtractFramesNode:
    def __init__(self):
        pass

    def calculate_max_frames(self, duration: float) -> int:
        """
        Quantity of frames to sample based on duration.
        Logic: 1 frame every ~6s, minimum 8, maximum 20.
        """
        calculated = int(duration / 6)
        return max(8, min(calculated, 20))

    def extract_frames(self, state: GraphMessage) -> GraphMessage:
        frames_dir = f"./tmp/gym_frames_{os.getpid()}"
        os.makedirs(frames_dir, exist_ok=True)

        duration = state.get("duration")
        max_frames = self.calculate_max_frames(duration)

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
                state.get("video_path"),
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

        return {"frames_dir": frames_dir, "frames": frames}
