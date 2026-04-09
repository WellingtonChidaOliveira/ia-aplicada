import json
from pathlib import Path 
import handlers.videos.get_video as get_video
import handlers.videos.get_video_duration as get_video_duration
import handlers.videos.extract_frames as extract_frames
import handlers.videos.resize_frames as resize_frames

video_path = Path("~/Documents/projects/ia/ia-aplicada/video_cut/video.mp4").expanduser()
frames_path = Path("~/Documents/projects/ia/ia-aplicada/video_cut/frames").expanduser()

streams = get_video.get_video(video_path)

duration, fps = get_video_duration.get_video_duration(streams)

print(f"Duration: {duration}, FPS: {fps}")

frames = extract_frames.extract_frames(video_path, frames_path, fps=1)

resize_frames.resize_frames(frames_path, frames_path, size=(1280, 720))