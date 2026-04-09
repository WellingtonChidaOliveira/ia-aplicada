import os
import subprocess

def extract_frames(video_path, output_folder, fps=1):
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    cmd = [
        "ffmpeg",
        "-i", video_path,
        "-vf", f"fps={fps}",
        f"{output_folder}/frame_%04d.jpg"
    ]
    subprocess.run(cmd, capture_output=True, text=True)
    return [f for f in os.listdir(output_folder) if f.endswith(".jpg")]

