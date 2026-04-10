from pathlib import Path
import handlers.videos.get_video as get_video
import handlers.videos.get_video_duration as get_video_duration
import handlers.videos.extract_frames as extract_frames
import handlers.videos.resize_frames as resize_frames
import service.ollama as ollama

video_path = Path(
    "~/Documents/projects/ia/ia-aplicada/video_cut/video.mp4"
).expanduser()
frames_path = Path("~/Documents/projects/ia/ia-aplicada/video_cut/frames").expanduser()

streams = get_video.get_video(video_path)

duration, fps = get_video_duration.get_video_duration(streams)

print(f"Duration: {duration}, FPS: {fps}")

try:
    frames = extract_frames.extract_frames(video_path, frames_path, fps=1)
    print(f"Frames extracted: {len(frames)}")

    resize_frames.resize_frames(frames_path, frames_path, size=(1280, 720))

    print(f"Frames resized: {len(frames)}")

    analise = ollama.analise_video(frames, frames_path)
    print(analise)

    # trecho = ollama.decidir_trecho(analise, duration)
    # print(json.dumps(trecho, indent=2))

except Exception as e:
    print(e)


# import requests
# import base64


# def carregar_base64(path: str) -> str:
#     with open(path, "rb") as f:
#         return base64.b64encode(f.read()).decode("utf-8")


# # testa com UM frame só primeiro
# img = carregar_base64(
#     "/home/wchida/Documents/projects/ia/ia-aplicada/video_cut/frames/frame_0021.jpg"
# )

# payload = {
#     "model": "qwen3-vl:8b",
#     "prompt": "Descreva o que você vê nesta imagem.",
#     "images": [img],
#     "stream": False,
#     "options": {
#         "temperature": 0.2,
#         "num_predict": 512,
#     },
# }

# response = requests.post(
#     "http://localhost:11434/api/generate", json=payload, timeout=600
# )

# print(response.json()["response"])
