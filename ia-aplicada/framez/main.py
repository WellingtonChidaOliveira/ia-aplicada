from pathlib import Path
from agent.factory import CreateGraph
from service.llmRouter import LLMClient


def execute(video_path: Path):
    if not video_path.exists():
        raise FileNotFoundError(f"Video not found: {video_path}")

    client = LLMClient()

    graph = CreateGraph(video_path, client)
    graph.invoke({"messages": [{"role": "user", "content": "s"}]})


if __name__ == "__main__":
    execute(Path("./videos/IMG_7877.mp4"))
