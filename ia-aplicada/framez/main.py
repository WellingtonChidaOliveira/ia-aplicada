from pathlib import Path
from agent.factory import CreateGraph
from service.llmRouter import LLMClient

video_path = Path("./videos/IMG_7878.mp4")
client = LLMClient()

graph = CreateGraph(video_path, client)
graph.invoke({"messages": [{"role": "user", "content": "run"}]})
