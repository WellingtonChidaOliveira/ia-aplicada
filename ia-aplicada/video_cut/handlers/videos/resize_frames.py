import os
import subprocess

def resize_frames(frames_path, output_folder, size=(1280, 720)):
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    for frame in os.listdir(frames_path):
        if frame.endswith(".jpg"):
            cmd = [
                "ffmpeg",
                "-i", f"{frames_path}/{frame}",
                "-vf", f"scale={size[0]}:{size[1]}",
                f"{output_folder}/{frame}"
            ]
            subprocess.run(cmd, capture_output=True, text=True)
    return [f for f in os.listdir(output_folder) if f.endswith(".jpg")]
