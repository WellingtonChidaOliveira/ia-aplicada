from pathlib import Path
from service.llmRouter import LLMClient
from service.langgraph import start_graph


class AgentFactory:
    def __init__(self, path: str | None = None, client: LLMClient | None = None):
        self.client = client if client else LLMClient()
        self.path = path if path else None
        self.msg = ""

    def start_service(self):
        print("Welcome to framez")
        if self.path is None:
            self.path = input("Enter the path to the video: ")

        self.path = Path.cwd() / "videos" / self.path
        if not self.path.exists():
            self.msg = "skip"
            print(f"Video not found: {self.path}")
            # raise FileNotFoundError(f"Video not found: {self.path}")

        client = LLMClient()

        graph = CreateGraph(self.path, client)
        graph.invoke({"messages": [{"role": "user", "content": self.msg}]})


def CreateGraph(path: str, client):
    return start_graph(path, client)
