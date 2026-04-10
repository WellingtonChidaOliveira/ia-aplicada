from pathlib import Path
from agent.factory import CreateGraph

video_path = Path("./videos/video.mp4")

graph = CreateGraph(video_path)
graph.invoke({"messages": [{"role": "user", "content": "hi!"}]})
