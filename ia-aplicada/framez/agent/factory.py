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

        # self.path = Path.cwd() / "videos" / self.path / "tr.mp4"
        self.path = Path("./videos/tr.mp4")
        if not self.path.exists():
            self.msg = "skip"
            print(f"Video not found: {self.path}")

        client = LLMClient()

        graph = start_graph(self.path, client)
        return graph


# Top-level factory for LangGraph API/Studio.
# Must accept NO arguments (or only RunnableConfig) — the server uses
# Python inspect to validate the signature and rejects anything else.
# path and client are fetched lazily inside the graph nodes from the state.
def CreateGraph():
    return start_graph(Path("./videos/tr.mp4"), LLMClient())
